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


class HasXFormObjectPermissionMixin(object):
    """Use XForm permissions for Attachment objects"""
    def has_permission(self, request, view):
        model_cls = None

        # Workaround to ensure DjangoModelPermissions are not applied
        # to the root view when using DefaultRouter.
        if (model_cls is None and
                getattr(view, '_ignore_model_permissions', False)):
            return True

        model_cls = XForm
        perms = self.get_required_permissions(request.method, model_cls)

        if (request.user and
                (request.user.is_authenticated() or
                 not self.authenticated_users_only) and
                request.user.has_perms(perms)):

            return True

        return False


class MetaDataObjectPermissions(HasXFormObjectPermissionMixin,
                                DjangoObjectPermissions):

    def has_object_permission(self, request, view, obj):

        # Originally they monkey patched the permissions object this way:
        # view.model = XForm
        # It was already a hack for some permission workaround
        # (https://github.com/kobotoolbox/kobocat/commit/106c0cbef2ecec9448df1baab7333391972730f8)
        # It doesn't work with DRF 3 because the model class is retrieved
        # using get_queryset. We should replace this hack by something
        # cleaner, but that would need to rework the entire permissions system
        # so instead, we are keeping the spirit of the original hack
        # by temporarily patching get_queryset.

        # save all get_queryset to restore it later
        old_get_qs = view.get_queryset

        # has_object_permission() will do get_queryset().model to get XForm
        def get_queryset(*args, **kwargs):
            return XForm.objects.all()

        # patching the method
        view.get_queryset = get_queryset

        # now getting the perm works
        parent = super(MetaDataObjectPermissions, self)
        has_perm = parent.has_object_permission(request, view, obj.xform)

        # putting the true get_queryset back
        view.get_queryset = old_get_qs
        return has_perm


class AttachmentObjectPermissions(DjangoObjectPermissions):

    def __init__(self, *args, **kwargs):
        # The default `perms_map` does not include GET, OPTIONS, PATCH or HEAD. See
        # http://www.django-rest-framework.org/api-guide/filtering/#djangoobjectpermissionsfilter
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
