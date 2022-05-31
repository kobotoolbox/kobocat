# coding: utf-8
import json
import os
from datetime import datetime

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.storage import get_storage_class
from django.http import Http404, HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils import six
from django.utils.translation import gettext as t
from rest_framework import exceptions
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.viewsets import ModelViewSet

from onadata.apps.api import tools as utils
from onadata.apps.api.permissions import XFormPermissions
from onadata.apps.logger.models.xform import XForm
from onadata.apps.viewer.models.export import Export
from onadata.libs import filters
from onadata.libs.exceptions import NoRecordsFoundError
from onadata.libs.mixins.anonymous_user_public_forms_mixin import (
    AnonymousUserPublicFormsMixin)
from onadata.libs.mixins.labels_mixin import LabelsMixin
from onadata.libs.renderers import renderers
from onadata.libs.serializers.xform_serializer import XFormSerializer
from onadata.libs.utils import log
from onadata.libs.utils.common_tags import SUBMISSION_TIME
from onadata.libs.utils.csv_import import submit_csv
from onadata.libs.utils.export_tools import generate_export, \
    should_create_new_export
from onadata.libs.utils.export_tools import newset_export_for
from onadata.libs.utils.logger_tools import response_with_mimetype_and_name
from onadata.libs.utils.string import str2bool
from onadata.libs.utils.viewer_tools import _get_form_url
from onadata.libs.utils.viewer_tools import enketo_url, EnketoError

EXPORT_EXT = {
    'xls': Export.XLS_EXPORT,
    'xlsx': Export.XLS_EXPORT,
    'csv': Export.CSV_EXPORT,
}


def _get_export_type(export_type):
    if export_type in EXPORT_EXT.keys():
        export_type = EXPORT_EXT[export_type]
    else:
        raise exceptions.ParseError(
            t("'%(export_type)s' format not known or not implemented!" %
              {'export_type': export_type})
        )

    return export_type


def _get_extension_from_export_type(export_type):
    extension = export_type

    if export_type == Export.XLS_EXPORT:
        extension = 'xlsx'

    return extension


def _set_start_end_params(request, query):
    format_date_for_mongo = lambda x, datetime: datetime.strptime(
        x, '%y_%m_%d_%H_%M_%S').strftime('%Y-%m-%dT%H:%M:%S')

    # check for start and end params
    if 'start' in request.GET or 'end' in request.GET:
        query = json.loads(query) \
            if isinstance(query, six.string_types) else query
        query[SUBMISSION_TIME] = {}

        try:
            if request.GET.get('start'):
                query[SUBMISSION_TIME]['$gte'] = format_date_for_mongo(
                    request.GET['start'], datetime)

            if request.GET.get('end'):
                query[SUBMISSION_TIME]['$lte'] = format_date_for_mongo(
                    request.GET['end'], datetime)
        except ValueError:
            raise exceptions.ParseError(
                t("Dates must be in the format YY_MM_DD_hh_mm_ss")
            )
        else:
            query = json.dumps(query)

        return query


def _generate_new_export(request, xform, query, export_type):
    query = _set_start_end_params(request, query)
    extension = _get_extension_from_export_type(export_type)

    try:
        export = generate_export(
            export_type, extension, xform.user.username,
            xform.id_string, None, query
        )
        audit = {
            "xform": xform.id_string,
            "export_type": export_type
        }
        log.audit_log(
            log.Actions.EXPORT_CREATED, request.user, xform.user,
            t("Created %(export_type)s export on '%(id_string)s'.") %
            {
                'id_string': xform.id_string,
                'export_type': export_type.upper()
            }, audit, request)
    except NoRecordsFoundError:
        raise Http404(t("No records found to export"))
    else:
        return export


def _get_user(username):
    users = User.objects.filter(username=username)

    return users.count() and users[0] or None


def _get_owner(request):
    owner = request.data.get('owner') or request.user

    if isinstance(owner, six.string_types):
        owner = _get_user(owner)

        if owner is None:
            raise ValidationError(
                "User with username %(owner)s does not exist."
            )

    return owner


def response_for_format(form, format=None):
    if format == 'xml':
        formatted_data = form.xml
    elif format == 'xls':
        file_path = form.xls.name
        default_storage = get_storage_class()()
        if file_path != '' and default_storage.exists(file_path):
            formatted_data = form.xls
        else:
            raise Http404(t("No XLSForm found."))
    else:
        formatted_data = json.loads(form.json)
    return Response(formatted_data)


def should_regenerate_export(xform, export_type, request):
    return should_create_new_export(xform, export_type) or\
        'start' in request.GET or 'end' in request.GET or\
        'query' in request.GET


def value_for_type(form, field, value):
    if form._meta.get_field(field).get_internal_type() == 'BooleanField':
        return str2bool(value)

    return value


def log_export(request, xform, export_type):
    # log download as well
    audit = {
        "xform": xform.id_string,
        "export_type": export_type
    }
    log.audit_log(
        log.Actions.EXPORT_DOWNLOADED, request.user, xform.user,
        t("Downloaded %(export_type)s export on '%(id_string)s'.") %
        {
            'id_string': xform.id_string,
            'export_type': export_type.upper()
        }, audit, request)


def custom_response_handler(request, xform, query, export_type):
    export_type = _get_export_type(export_type)

    # check if we need to re-generate,
    # we always re-generate if a filter is specified
    if should_regenerate_export(xform, export_type, request):
        export = _generate_new_export(request, xform, query, export_type)
    else:
        export = newset_export_for(xform, export_type)
        if not export.filename:
            # tends to happen when using newset_export_for.
            export = _generate_new_export(request, xform, query, export_type)

    log_export(request, xform, export_type)

    # get extension from file_path, exporter could modify to
    # xlsx if it exceeds limits
    path, ext = os.path.splitext(export.filename)
    ext = ext[1:]
    id_string = None if request.GET.get('raw') else xform.id_string
    response = response_with_mimetype_and_name(
        Export.EXPORT_MIMES[ext], id_string, extension=ext,
        file_path=export.filepath)

    return response


class XFormViewSet(AnonymousUserPublicFormsMixin, LabelsMixin, ModelViewSet):

    """
Publish XLSForms, List, Retrieve Published Forms.

Where:

- `pk` - is the form unique identifier

## Upload XLSForm

To publish and xlsform, you need to provide either the xlsform via `xls_file` \
parameter or a link to the xlsform via the `xls_url` parameter.
Optionally, you can specify the target account where the xlsform should be \
published using the `owner` parameter, which specifies the username to the
account.

- `xls_file`: the xlsform file.
- `owner`: username to the target account (Optional)

<pre class="prettyprint">
<b>POST</b> /api/v1/forms</pre>
> Example
>
>       curl -X POST -F xls_file=@/path/to/form.xls \
https://example.com/api/v1/forms
>

> Response
>
>       {
>           "url": "https://example.com/api/v1/forms/28058",
>           "formid": 28058,
>           "uuid": "853196d7d0a74bca9ecfadbf7e2f5c1f",
>           "id_string": "Birds",
>           "title": "Birds",
>           "description": "",
>           "downloadable": true,
>           "encrypted": false,
>           "owner": "ona",
>           "public": false,
>           "public_data": false,
>           "date_created": "2013-07-25T14:14:22.892Z",
>           "date_modified": "2013-07-25T14:14:22.892Z"
>       }

## Get list of forms

<pre class="prettyprint">
<b>GET</b> /api/v1/forms</pre>

> Request
>
>       curl -X GET https://example.com/api/v1/forms


## Get list of forms filter by owner

<pre class="prettyprint">
<b>GET</b> /api/v1/forms?<code>owner</code>=<code>owner_username</code></pre>

> Request
>
>       curl -X GET https://example.com/api/v1/forms?owner=ona

## Get list of forms filtered by id_string

<pre class="prettyprint">
<b>GET</b> /api/v1/forms?<code>id_string</code>=<code>form_id_string</code></pre>

> Request
>
>       curl -X GET https://example.com/api/v1/forms?id_string=Birds

## Get Form Information

<pre class="prettyprint">
<b>GET</b> /api/v1/forms/<code>{pk}</code></pre>

> Example
>
>       curl -X GET https://example.com/api/v1/forms/28058

> Response
>
>       {
>           "url": "https://example.com/api/v1/forms/28058",
>           "formid": 28058,
>           "uuid": "853196d7d0a74bca9ecfadbf7e2f5c1f",
>           "id_string": "Birds",
>           "title": "Birds",
>           "description": "",
>           "downloadable": true,
>           "encrypted": false,
>           "owner": "https://example.com/api/v1/users/ona",
>           "public": false,
>           "public_data": false,
>           "require_auth": false,
>           "date_created": "2013-07-25T14:14:22.892Z",
>           "date_modified": "2013-07-25T14:14:22.892Z"
>       }

## Set Form Information

You can use `PUT` or `PATCH` http methods to update or set form data elements.
If you are using `PUT`, you have to provide the `uuid, description,
downloadable, owner, public, public_data, title` fields. With `PATCH` you only
need provide at least one of the fields.

<pre class="prettyprint">
<b>PATCH</b> /api/v1/forms/<code>{pk}</code></pre>

> Example
>
>       curl -X PATCH -d "public=True" -d "description=Le description"\
https://example.com/api/v1/forms/28058

> Response
>
>       {
>           "url": "https://example.com/api/v1/forms/28058",
>           "formid": 28058,
>           "uuid": "853196d7d0a74bca9ecfadbf7e2f5c1f",
>           "id_string": "Birds",
>           "title": "Birds",
>           "description": "Le description",
>           "downloadable": true,
>           "encrypted": false,
>           "owner": "https://example.com/api/v1/users/ona",
>           "public": true,
>           "public_data": false,
>           "date_created": "2013-07-25T14:14:22.892Z",
>           "date_modified": "2013-07-25T14:14:22.892Z"
>       }

## Update Form

You may overwrite the form's contents while preserving its submitted data,
`id_string` and all other attributes, by sending a `PATCH` that includes
`xls_file`. Use with caution, as this may compromise the
methodology of your study!

<pre class="prettyprint">
<b>PATCH</b> /api/v1/forms/<code>{pk}</code></pre>

> Example
>
>       curl -X PATCH -F xls_file=@/path/to/form.xls \
https://example.com/api/v1/forms/28058

## Delete Form

<pre class="prettyprint">
<b>DELETE</b> /api/v1/forms/<code>{pk}</code></pre>
> Example
>
>       curl -X DELETE https://example.com/api/v1/forms/28058
>
> Response
>
>       HTTP 204 NO CONTENT

## List Forms
<pre class="prettyprint">
<b>GET</b> /api/v1/forms
</pre>
> Example
>
>       curl -X GET https://example.com/api/v1/forms

> Response
>
>       [{
>           "url": "https://example.com/api/v1/forms/28058",
>           "formid": 28058,
>           "uuid": "853196d7d0a74bca9ecfadbf7e2f5c1f",
>           "id_string": "Birds",
>           "title": "Birds",
>           ...
>       }, ...]

## Get `JSON` | `XML` | `XLS` Form Representation
<pre class="prettyprint">
<b>GET</b> /api/v1/forms/<code>{pk}</code>/form.\
<code>{format}</code></pre>
> JSON Example
>
>       curl -X GET https://example.com/api/v1/forms/28058/form.json

> Response
>
>        {
>            "name": "Birds",
>            "title": "Birds",
>            "default_language": "default",
>            "id_string": "Birds",
>            "type": "survey",
>            "children": [
>                {
>                    "type": "text",
>                    "name": "name",
>                    "label": "1. What is your name?"
>                },
>                ...
>                ]
>        }

> XML Example
>
>       curl -X GET https://example.com/api/v1/forms/28058/form.xml

> Response
>
>        <?xml version="1.0" encoding="utf-8"?>
>        <h:html xmlns="http://www.w3.org/2002/xforms" ...>
>          <h:head>
>            <h:title>Birds</h:title>
>            <model>
>              <itext>
>                 .....
>          </h:body>
>        </h:html>

> XLS Example
>
>       curl -X GET https://example.com/api/v1/forms/28058/form.xls

> Response
>
>       Xls file downloaded

## Get list of forms with specific tag(s)

Use the `tags` query parameter to filter the list of forms, `tags` should be a
comma separated list of tags.

<pre class="prettyprint">
<b>GET</b> /api/v1/forms?<code>tags</code>=<code>tag1,tag2</code></pre>

List forms tagged `smart` or `brand new` or both.
> Request
>
>       curl -X GET https://example.com/api/v1/forms?tag=smart,brand+new

> Response
>        HTTP 200 OK
>
>       [{
>           "url": "https://example.com/api/v1/forms/28058",
>           "formid": 28058,
>           "uuid": "853196d7d0a74bca9ecfadbf7e2f5c1f",
>           "id_string": "Birds",
>           "title": "Birds",
>           ...
>       }, ...]


## Get list of Tags for a specific Form
<pre class="prettyprint">
<b>GET</b> /api/v1/forms/<code>{pk}</code>/labels
</pre>
> Request
>
>       curl -X GET https://example.com/api/v1/forms/28058/labels

> Response
>
>       ["old", "smart", "clean house"]

## Tag forms

A `POST` payload of parameter `tags` with a comma separated list of tags.

Examples

- `animal fruit denim` - space delimited, no commas
- `animal, fruit denim` - comma delimited

<pre class="prettyprint">
<b>POST</b> /api/v1/forms/<code>{pk}</code>/labels
</pre>

Payload

    {"tags": "tag1, tag2"}

## Delete a specific tag

<pre class="prettyprint">
<b>DELETE</b> /api/v1/forms/<code>{pk}</code>/labels/<code>tag_name</code>
</pre>

> Request
>
>       curl -X DELETE \
https://example.com/api/v1/forms/28058/labels/tag1
>
> or to delete the tag "hello world"
>
>       curl -X DELETE \
https://example.com/api/v1/forms/28058/labels/hello%20world
>
> Response
>
>        HTTP 200 OK

## Get webform/enketo link

<pre class="prettyprint">
<b>GET</b> /api/v1/forms/<code>{pk}</code>/enketo</pre>

> Request
>
>       curl -X GET \
https://example.com/api/v1/forms/28058/enketo
>
> Response
>
>       {"enketo_url": "https://h6ic6.enketo.org/webform"}
>
>        HTTP 200 OK

## Get form data in xls, csv format.

Get form data exported as xls, csv, csv zip, sav zip format.

Where:

- `pk` - is the form unique identifier
- `format` - is the data export format i.e csv, xls, csvzip, savzip

<pre class="prettyprint">
<b>GET</b> /api/v1/forms/{pk}.{format}</code>
</pre>
> Example
>
>       curl -X GET https://example.com/api/v1/forms/28058.xls

> Binary file export of the format specified is returned as the response for
>the download.
>
> Response
>
>        HTTP 200 OK

## Import CSV data to existing form

- `csv_file` a valid csv file with exported \
data (instance/submission per row)

<pre class="prettyprint">
<b>GET</b> /api/v1/forms/<code>{pk}</code>/csv_import
</pre>

> Example
>
>       curl -X POST https://example.com/api/v1/forms/123/csv_import \
-F csv_file=@/path/to/csv_import.csv
>
> Response
>
>        HTTP 200 OK
>       {
>           "additions": 9,
>           "updates": 0
>       }
"""
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES + [
        renderers.XLSRenderer,
        renderers.XLSXRenderer,
        renderers.CSVRenderer,
        renderers.RawXMLRenderer
    ]
    queryset = XForm.objects.all()
    serializer_class = XFormSerializer
    lookup_field = 'pk'
    extra_lookup_fields = None
    permission_classes = [XFormPermissions, ]
    filter_backends = (filters.AnonDjangoObjectPermissionFilter,
                       filters.TagFilter,
                       filters.XFormOwnerFilter,
                       filters.XFormIdStringFilter)

    def create(self, request, *args, **kwargs):
        owner = _get_owner(request)
        survey = utils.publish_xlsform(request, owner)

        if isinstance(survey, XForm):
            xform = XForm.objects.get(pk=survey.pk)
            # The XForm has been created, but `publish_xlsform` relies on
            # `onadata.apps.main.forms.QuickConverterForm`, which uses standard
            # Django forms and only recognizes the `xls_file` fields.
            # Use the DRF serializer to update the XForm with values for other
            # fields.
            serializer = XFormSerializer(
                xform,
                data=request.data,
                context={'request': request},
                partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED,
                            headers=headers)

        return Response(survey, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['GET'])
    def enketo(self, request, **kwargs):
        self.object = self.get_object()
        form_url = _get_form_url(self.object.user.username)

        data = {'message': t("Enketo not properly configured.")}
        http_status = status.HTTP_400_BAD_REQUEST

        try:
            url = enketo_url(form_url, self.object.id_string)
        except EnketoError:
            pass
        else:
            if url:
                http_status = status.HTTP_200_OK
                data = {"enketo_url": url}

        return Response(data, http_status)

    def update(self, request, pk, *args, **kwargs):
        if 'xls_file' in request.FILES:
            # A new XLSForm has been uploaded and will replace the existing
            # form
            existing_xform = get_object_or_404(XForm, pk=pk)
            # Behave like `onadata.apps.main.views.update_xform`: only allow
            # the update to proceed if the user is the owner
            owner = existing_xform.user
            if request.user.pk != owner.pk:
                raise exceptions.PermissionDenied(
                    detail=t("Only a form's owner can overwrite its contents"))
            survey = utils.publish_xlsform(request, owner, existing_xform)
            if not isinstance(survey, XForm):
                if isinstance(survey, dict) and 'text' in survey:
                    # Typical error text; pass it along
                    raise exceptions.ParseError(detail=survey['text'])
                else:
                    # Something odd; hopefully it can be coerced into a string
                    raise exceptions.ParseError(detail=survey)
        # Let the superclass handle updates to the other fields
        return super().update(request, pk, *args, **kwargs)

    @action(detail=True, methods=['GET'])
    def form(self, request, format='json', **kwargs):
        form = self.get_object()
        if format not in ['json', 'xml', 'xls', 'csv']:
            return HttpResponseBadRequest('400 BAD REQUEST',
                                          content_type='application/json',
                                          status=400)

        filename = form.id_string + "." + format
        response = response_for_format(form, format=format)
        response['Content-Disposition'] = 'attachment; filename=' + filename

        return response

    def retrieve(self, request, *args, **kwargs):
        xform = self.get_object()
        export_type = kwargs.get('format')
        query = request.GET.get('query', {})

        if export_type is None or export_type in ['json']:
            # perform default viewset retrieve, no data export
            return super().retrieve(request, *args, **kwargs)

        return custom_response_handler(request,
                                       xform,
                                       query,
                                       export_type)

    @action(detail=True, methods=['POST'])
    def csv_import(self, request, *args, **kwargs):
        """
        Endpoint for CSV data imports

        Calls :py:func:`onadata.libs.utils.csv_import.submit_csv`
        passing with the `request.FILES.get('csv_file')` upload for import.
        """
        xform = self.get_object()
        if request.user != xform.user:
            # Access control for this endpoint previously relied on testing
            # that the user had `logger.add_xform` on this specific XForm,
            # which is meaningless but does get assigned to the XForm owner by
            # the post-save signal handler
            # `onadata.apps.logger.models.xform.set_object_permissions()`.
            # For safety and clarity, this endpoint now explicitly denies
            # access to all non-owners.
            raise PermissionDenied
        resp = submit_csv(request, xform, request.FILES.get('csv_file'))
        return Response(
            data=resp,
            status=status.HTTP_200_OK if resp.get('error') is None else
            status.HTTP_400_BAD_REQUEST)
