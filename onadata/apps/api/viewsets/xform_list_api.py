import pytz

from datetime import datetime

from django.conf import settings
from django.http import Http404
from django.shortcuts import get_object_or_404

from rest_framework import viewsets
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.decorators import detail_route

from onadata.apps.api.tools import get_media_file_response
from onadata.apps.logger.models.xform import XForm
from onadata.apps.main.models.meta_data import MetaData
from onadata.apps.main.models.user_profile import UserProfile
from onadata.libs import filters
from onadata.libs.authentication import DigestAuthentication
from onadata.libs.renderers.renderers import MediaFileContentNegotiation
from onadata.libs.renderers.renderers import XFormListRenderer
from onadata.libs.renderers.renderers import XFormManifestRenderer
from onadata.libs.serializers.xform_serializer import XFormListSerializer
from onadata.libs.serializers.xform_serializer import XFormManifestSerializer


# 10,000,000 bytes
DEFAULT_CONTENT_LENGTH = getattr(settings, 'DEFAULT_CONTENT_LENGTH', 10000000)


class XFormListApi(viewsets.ReadOnlyModelViewSet):
    content_negotiation_class = MediaFileContentNegotiation
    filter_backends = (filters.XFormListObjectPermissionFilter,)
    queryset = XForm.objects.filter(downloadable=True)
    permission_classes = (permissions.AllowAny,)
    renderer_classes = (XFormListRenderer,)
    serializer_class = XFormListSerializer
    template_name = 'api/xformsList.xml'

    def __init__(self, *args, **kwargs):
        super(XFormListApi, self).__init__(*args, **kwargs)
        # Respect DEFAULT_AUTHENTICATION_CLASSES, but also ensure that the
        # previously hard-coded authentication classes are included first
        authentication_classes = [
            DigestAuthentication,
        ]
        self.authentication_classes = authentication_classes + [
            auth_class for auth_class in self.authentication_classes
                if not auth_class in authentication_classes
        ]

    def get_openrosa_headers(self):
        tz = pytz.timezone(settings.TIME_ZONE)
        dt = datetime.now(tz).strftime('%a, %d %b %Y %H:%M:%S %Z')

        return {
            'Date': dt,
            'X-OpenRosa-Version': '1.0',
            'X-OpenRosa-Accept-Content-Length': DEFAULT_CONTENT_LENGTH
        }

    def get_renderers(self):
        if self.action and self.action == 'manifest':
            return [XFormManifestRenderer()]

        return super(XFormListApi, self).get_renderers()

    def filter_queryset(self, queryset):
        username = self.kwargs.get('username')
        if username is None:
            # If no username is specified, the request must be authenticated
            if self.request.user.is_anonymous():
                # raises a permission denied exception, forces authentication
                self.permission_denied(self.request)
            else:
                # Return all the forms the currently-logged-in user can access,
                # including those shared by other users
                queryset = super(XFormListApi, self).filter_queryset(queryset)
        else:
            profile = get_object_or_404(
                UserProfile, user__username=username.lower()
            )
            # Include only the forms belonging to the specified user
            queryset = queryset.filter(user=profile.user)
            if profile.require_auth:
                # The specified has user ticked "Require authentication to see
                # forms and submit data"; reject anonymous requests
                if self.request.user.is_anonymous():
                    # raises a permission denied exception, forces
                    # authentication
                    self.permission_denied(self.request)
                else:
                    # Someone has logged in, but they are not necessarily
                    # allowed to access the forms belonging to the specified
                    # user. Filter again to consider object-level permissions
                    queryset = super(XFormListApi, self).filter_queryset(
                        queryset
                    )
        try:
            # https://docs.getodk.org/openrosa-form-list/#form-list-api says:
            #   `formID`: If specified, the server MUST return information for
            #   only this formID.
            id_string_filter = self.request.GET['formID']
        except KeyError:
            pass
        else:
            queryset = queryset.filter(id_string=id_string_filter)

        return queryset

    def list(self, request, *args, **kwargs):
        self.object_list = self.filter_queryset(self.get_queryset())

        serializer = self.get_serializer(self.object_list, many=True)

        return Response(serializer.data, headers=self.get_openrosa_headers())

    def retrieve(self, request, *args, **kwargs):
        self.object = self.get_object()

        return Response(self.object.xml, headers=self.get_openrosa_headers())

    @detail_route(methods=['GET'])
    def manifest(self, request, *args, **kwargs):
        self.object = self.get_object()
        object_list = MetaData.objects.filter(data_type='media',
                                              xform=self.object)
        context = self.get_serializer_context()
        serializer = XFormManifestSerializer(object_list, many=True,
                                             context=context)

        return Response(serializer.data, headers=self.get_openrosa_headers())

    @detail_route(methods=['GET'])
    def media(self, request, *args, **kwargs):
        self.object = self.get_object()
        pk = kwargs.get('metadata')

        if not pk:
            raise Http404()

        meta_obj = get_object_or_404(
            MetaData, data_type='media', xform=self.object, pk=pk)

        return get_media_file_response(meta_obj)
