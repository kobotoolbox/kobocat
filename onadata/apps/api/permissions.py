# coding: utf-8
from __future__ import unicode_literals, print_function, division, absolute_import

from rest_framework.permissions import (
    DjangoObjectPermissions,
    IsAuthenticated,
    SAFE_METHODS
)

from onadata.libs.constants import (
    CAN_CHANGE_XFORM,
    CAN_VALIDATE_XFORM,
    CAN_DELETE_DATA_XFORM,
)
from onadata.apps.logger.models import XForm


class ViewDjangoObjectPermissions(DjangoObjectPermissions):
    perms_map = {
        'GET': ['%(app_label)s.view_%(model_name)s'],
        'OPTIONS': [],
        'HEAD': [],
        'POST': ['%(app_label)s.add_%(model_name)s'],
        'PUT': ['%(app_label)s.change_%(model_name)s'],
        'PATCH': ['%(app_label)s.change_%(model_name)s'],
        'DELETE': ['%(app_label)s.delete_%(model_name)s'],
    }


class ObjectPermissionsWithViewRestricted(DjangoObjectPermissions):
    """
    The default `perms_map` does not include GET, OPTIONS, or HEAD, meaning
    anyone can view objects. We override this here to check for `view_…`
    permissions before allowing objects to be seen. Refer to
    https://www.django-rest-framework.org/api-guide/permissions/#djangoobjectpermissions
    """
    def __init__(self, *args, **kwargs):
        super(ObjectPermissionsWithViewRestricted, self).__init__(
            *args, **kwargs
        )
        # Do NOT mutate `perms_map` from the parent class! Doing so will affect
        # *every* instance of `DjangoObjectPermissions` and all its subclasses
        self.perms_map = self.perms_map.copy()
        self.perms_map['GET'] = ['%(app_label)s.view_%(model_name)s']
        self.perms_map['OPTIONS'] = ['%(app_label)s.view_%(model_name)s']
        self.perms_map['HEAD'] = ['%(app_label)s.view_%(model_name)s']

        # `PATCH` should already be set properly by DRF, but it used to be
        # explicitly assigned here as well. Double-check that it's right
        assert self.perms_map['PATCH'] == ['%(app_label)s.change_%(model_name)s']

    def get_required_permissions(self, method, model_cls):

        app_label = (
            model_cls._meta.app_label
            if not hasattr(self, 'APP_LABEL')
            else self.APP_LABEL
        )

        model_name = (
            model_cls._meta.model_name
            if not hasattr(self, 'MODEL_NAME')
            else self.MODEL_NAME
        )
        kwargs = {
            'app_label': app_label,
            'model_name': model_name
        }
        return [perm % kwargs for perm in self.perms_map[method]]

    def get_required_object_permissions(self, method, model_cls):
        return self.get_required_permissions(method, model_cls)

    authenticated_users_only = False


class XFormPermissions(ObjectPermissionsWithViewRestricted):

    def has_permission(self, request, view):
        # Allow anonymous users to access shared data
        if request.method in SAFE_METHODS and \
                view.action and view.action == 'retrieve':
            return True

        return super(XFormPermissions, self).has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        # Allow anonymous users to access shared data
        if request.method in SAFE_METHODS and view.action == 'retrieve':
            if obj.shared:
                return True

        return super(XFormPermissions, self).has_object_permission(
            request, view, obj)


class XFormDataPermissions(ObjectPermissionsWithViewRestricted):

    def __init__(self, *args, **kwargs):
        super(XFormDataPermissions, self).__init__(*args, **kwargs)
        # Those who can edit submissions can also delete them, following the
        # behavior of `onadata.apps.main.views.delete_data`
        self.perms_map = self.perms_map.copy()
        self.perms_map['DELETE'] = ['%(app_label)s.' + CAN_DELETE_DATA_XFORM]

    def has_permission(self, request, view):
        lookup_field = view.lookup_field
        lookup = view.kwargs.get(lookup_field)
        # Allow anonymous users to access access shared data
        allowed_anonymous_action = ['retrieve']
        if lookup:
            # We need to grant access to anonymous on list endpoint too when
            # a form pk is specified. e.g. `/api/v1/data/{pk}.json
            allowed_anonymous_action.append('list')
        if request.method in SAFE_METHODS and \
                view.action in allowed_anonymous_action:
            return True
        return super(XFormDataPermissions, self).has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        # Allow anonymous users to access shared data
        if request.method in SAFE_METHODS and \
                view.action in ['retrieve', 'list']:
            if obj.shared_data:
                return True

        if request.method == 'DELETE' and view.action == 'labels':
            user = request.user
            return user.has_perms([CAN_CHANGE_XFORM], obj)

        if request.method in ['PATCH', 'DELETE'] \
                and view.action.endswith('validation_status'):
            user = request.user
            return user.has_perms([CAN_VALIDATE_XFORM], obj)

        return super(XFormDataPermissions, self).has_object_permission(
            request, view, obj)


class MetaDataObjectPermissions(ObjectPermissionsWithViewRestricted):

    # Users can read MetaData objects with 'view_xform' permissions and
    # they can edit MetaData objects with 'change_xform'.
    # DRF get the app label and the model name from the queryset, so we
    # override them the find a match among user's XForm permissions.
    APP_LABEL = 'logger'
    MODEL_NAME = 'xform'

    def __init__(self, *args, **kwargs):
        super(MetaDataObjectPermissions, self).__init__(
            *args, **kwargs
        )
        self.perms_map = self.perms_map.copy()
        self.perms_map['POST'] = self.perms_map['PATCH']
        self.perms_map['PUT'] = self.perms_map['PATCH']
        self.perms_map['DELETE'] = self.perms_map['PATCH']

    def has_permission(self, request, view):

        allowed_anonymous_action = ['retrieve']

        try:
            request.GET['xform']
        except KeyError:
            pass
        else:
            # Allow anonymous user to list metadata when `xform` parameter is
            # specified.
            allowed_anonymous_action.append('list')

        if (
            request.method in SAFE_METHODS
            and view.action in allowed_anonymous_action
        ):
            return True

        return super(MetaDataObjectPermissions, self).has_permission(
            request=request, view=view
        )

    def has_object_permission(self, request, view, obj):

        # Grant access to publicly shared xforms.
        if (
            request.method in SAFE_METHODS
            and view.action == 'retrieve'
            and obj.xform.shared_data
        ):
            return True

        return super(MetaDataObjectPermissions, self).has_object_permission(
            request=request, view=view, obj=obj.xform
        )


class AttachmentObjectPermissions(DjangoObjectPermissions):

    def __init__(self, *args, **kwargs):
        # The default `perms_map` does not include GET, OPTIONS, PATCH or HEAD.
        # See http://www.django-rest-framework.org/api-guide/filtering/#djangoobjectpermissionsfilter  # noqa
        self.perms_map = DjangoObjectPermissions.perms_map.copy()
        self.perms_map['GET'] = ['%(app_label)s.view_xform']
        self.perms_map['OPTIONS'] = ['%(app_label)s.view_xform']
        self.perms_map['HEAD'] = ['%(app_label)s.view_xform']
        return super(AttachmentObjectPermissions, self).__init__(*args, **kwargs)

    def has_object_permission(self, request, view, obj):
        view.model = XForm

        return super(AttachmentObjectPermissions, self).has_object_permission(
            request, view, obj.instance.xform)


class NoteObjectPermissions(DjangoObjectPermissions):

    authenticated_users_only = False

    def __init__(self, *args, **kwargs):
        self.perms_map = self.perms_map.copy()
        self.perms_map['GET'] = ['%(app_label)s.view_xform']
        self.perms_map['OPTIONS'] = ['%(app_label)s.view_xform']
        self.perms_map['HEAD'] = ['%(app_label)s.view_xform']
        self.perms_map['PATCH'] = ['%(app_label)s.change_xform']
        self.perms_map['POST'] = ['%(app_label)s.change_xform']
        self.perms_map['DELETE'] = ['%(app_label)s.change_xform']

        return super(NoteObjectPermissions, self).__init__(*args, **kwargs)

    def has_permission(self, request, view):
        # Data will be filtered in `NoteViewSet`
        if request.method in SAFE_METHODS and view.action == 'retrieve':
            return True

        return super(NoteObjectPermissions, self).has_permission(request, view)

    def has_object_permission(self, request, view, obj):

        xform = obj.instance.xform

        # Allow anonymous users to access shared data
        if request.method in SAFE_METHODS and view.action == 'retrieve':
            if xform.shared_data:
                return True

        return super(NoteObjectPermissions, self).has_object_permission(
            request, view, xform)


class ConnectViewsetPermissions(IsAuthenticated):

    def has_permission(self, request, view):
        if view.action == 'reset':
            return True

        return super(ConnectViewsetPermissions, self)\
            .has_permission(request, view)


__permissions__ = [DjangoObjectPermissions, IsAuthenticated]
