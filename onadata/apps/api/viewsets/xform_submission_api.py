import re
import StringIO

from django.conf import settings
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _
from django.utils.decorators import method_decorator
from django.db import transaction

from rest_framework import permissions
from rest_framework import status
from rest_framework import viewsets
from rest_framework import mixins
from rest_framework.authentication import (
    BasicAuthentication,
    TokenAuthentication,
    SessionAuthentication,)
from rest_framework.response import Response
from rest_framework.renderers import BrowsableAPIRenderer, JSONRenderer
from onadata.apps.logger.models import Instance
from onadata.apps.main.models.user_profile import UserProfile
from onadata.libs import filters
from onadata.libs.authentication import DigestAuthentication
from onadata.libs.mixins.openrosa_headers_mixin import OpenRosaHeadersMixin
from onadata.libs.renderers.renderers import TemplateXMLRenderer
from onadata.libs.serializers.data_serializer import SubmissionSerializer
from onadata.libs.utils.logger_tools import dict2xform, safe_create_instance


# 10,000,000 bytes
DEFAULT_CONTENT_LENGTH = getattr(settings, 'DEFAULT_CONTENT_LENGTH', 10000000)
xml_error_re = re.compile('>(.*)<')


def is_json(request):
    return 'application/json' in request.content_type.lower()


def dict_lists2strings(d):
    """Convert lists in a dict to joined strings.

    :param d: The dict to convert.
    :returns: The converted dict."""
    for k, v in d.items():
        if isinstance(v, list) and all([isinstance(e, basestring) for e in v]):
            d[k] = ' '.join(v)
        elif isinstance(v, dict):
            d[k] = dict_lists2strings(v)

    return d


def create_instance_from_xml(username, request):
    xml_file_list = request.FILES.pop('xml_submission_file', [])
    xml_file = xml_file_list[0] if len(xml_file_list) else None
    media_files = request.FILES.values()

    return safe_create_instance(username, xml_file, media_files, None, request)


def create_instance_from_json(username, request):
    request.accepted_renderer = JSONRenderer()
    request.accepted_media_type = JSONRenderer.media_type
    dict_form = request.data
    submission = dict_form.get('submission')

    if submission is None:
        # return an error
        return [_(u"No submission key provided."), None]

    # convert lists in submission dict to joined strings
    submission_joined = dict_lists2strings(submission)
    xml_string = dict2xform(submission_joined, dict_form.get('id'))

    xml_file = StringIO.StringIO(xml_string)

    return safe_create_instance(username, xml_file, [], None, request)


class XFormSubmissionApi(OpenRosaHeadersMixin,
                         mixins.CreateModelMixin, viewsets.GenericViewSet):
    """
Implements OpenRosa Api [FormSubmissionAPI](\
    https://bitbucket.org/javarosa/javarosa/wiki/FormSubmissionAPI)

## Submit an XML XForm submission

<pre class="prettyprint">
<b>POST</b> /api/v1/submissions</pre>
> Example
>
>       curl -X POST -F xml_submission_file=@/path/to/submission.xml \
https://example.com/api/v1/submissions

## Submit an JSON XForm submission

<pre class="prettyprint">
<b>POST</b> /api/v1/submissions</pre>
> Example
>
>       curl -X POST -d '{"id": "[form ID]", "submission": [the JSON]} \
http://localhost:8000/api/v1/submissions -u user:pass -H "Content-Type: \
application/json"

Here is some example JSON, it would replace `[the JSON]` above:
>       {
>           "transport": {
>               "available_transportation_types_to_referral_facility": \
["ambulance", "bicycle"],
>               "loop_over_transport_types_frequency": {
>                   "ambulance": {
>                       "frequency_to_referral_facility": "daily"
>                   },
>                   "bicycle": {
>                       "frequency_to_referral_facility": "weekly"
>                   },
>                   "boat_canoe": null,
>                   "bus": null,
>                   "donkey_mule_cart": null,
>                   "keke_pepe": null,
>                   "lorry": null,
>                   "motorbike": null,
>                   "taxi": null,
>                   "other": null
>               }
>           }
>           "meta": {
>               "instanceID": "uuid:f3d8dc65-91a6-4d0f-9e97-802128083390"
>           }
>       }
"""
    filter_backends = (filters.AnonDjangoObjectPermissionFilter,)
    model = Instance
    permission_classes = (permissions.AllowAny,)
    renderer_classes = (TemplateXMLRenderer,
                        JSONRenderer,
                        BrowsableAPIRenderer)
    serializer_class = SubmissionSerializer
    template_name = 'submission.xml'

    def __init__(self, *args, **kwargs):
        super(XFormSubmissionApi, self).__init__(*args, **kwargs)
        # Respect DEFAULT_AUTHENTICATION_CLASSES, but also ensure that the
        # previously hard-coded authentication classes are included first
        authentication_classes = [
            DigestAuthentication,
            BasicAuthentication,
            TokenAuthentication
        ]
        # Do not use `SessionAuthentication`, which implicitly requires CSRF prevention
        # (which in turn requires that the CSRF token be submitted as a cookie and in the 
        # body of any "unsafe" requests).
        if SessionAuthentication in self.authentication_classes:
            self.authentication_classes.remove(SessionAuthentication)
        # We include BasicAuthentication here to allow submissions using basic
        # authentication over unencrypted HTTP. REST framework stops after the
        # first class that successfully authenticates, so
        # HttpsOnlyBasicAuthentication will be ignored even if included by
        # DEFAULT_AUTHENTICATION_CLASSES.
        self.authentication_classes = authentication_classes + [
            auth_class for auth_class in self.authentication_classes
                if not auth_class in authentication_classes
        ]

    def create(self, request, *args, **kwargs):
        username = self.kwargs.get('username')

        if self.request.user.is_anonymous():
            if username is None:
                # raises a permission denied exception, forces authentication
                self.permission_denied(self.request)
            else:
                user = get_object_or_404(User, username=username.lower())

                profile, created = UserProfile.objects.get_or_create(user=user)

                if profile.require_auth:
                    # raises a permission denied exception,
                    # forces authentication
                    self.permission_denied(self.request)
        elif not username:
            # get the username from the user if not set
            username = (request.user and request.user.username)

        if request.method.upper() == 'HEAD':
            return Response(status=status.HTTP_204_NO_CONTENT,
                            headers=self.get_openrosa_headers(request),
                            template_name=self.template_name)

        is_json_request = is_json(request)

        error, instance = (create_instance_from_json if is_json_request else
                           create_instance_from_xml)(username, request)

        if error or not instance:
            return self.error_response(error, is_json_request, request)

        context = self.get_serializer_context()
        serializer = SubmissionSerializer(instance, context=context)

        return Response(serializer.data,
                        headers=self.get_openrosa_headers(request),
                        status=status.HTTP_201_CREATED,
                        template_name=self.template_name)

    def error_response(self, error, is_json_request, request):
        if not error:
            error_msg = _(u"Unable to create submission.")
            status_code = status.HTTP_400_BAD_REQUEST
        elif isinstance(error, basestring):
            error_msg = error
            status_code = status.HTTP_400_BAD_REQUEST
        elif not is_json_request:
            return error
        else:
            error_msg = xml_error_re.search(error.content).groups()[0]
            status_code = error.status_code

        return Response({'error': error_msg},
                        headers=self.get_openrosa_headers(request),
                        status=status_code)
