from rest_framework.generics import get_object_or_404
from rest_framework.permissions import DjangoObjectPermissions
from rest_framework.permissions import IsAuthenticated

from onadata.libs.permissions import CAN_ADD_XFORM_TO_PROFILE
from onadata.libs.permissions import CAN_CHANGE_XFORM, CAN_VALIDATE_XFORM
from onadata.apps.api.tools import get_user_profile_or_none, \
    check_inherit_permission_from_project
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


class DjangoObjectPermissionsAllowAnon(DjangoObjectPermissions):
    authenticated_users_only = False


class XFormPermissions(DjangoObjectPermissions):

    authenticated_users_only = False

    def __init__(self, *args, **kwargs):
        # The default `perms_map` does not include GET, OPTIONS, PATCH or HEAD. See
        # http://www.django-rest-framework.org/api-guide/filtering/#djangoobjectpermissionsfilter
        self.perms_map['GET'] = ['%(app_label)s.view_%(model_name)s']
        self.perms_map['OPTIONS'] = ['%(app_label)s.view_%(model_name)s']
        self.perms_map['HEAD'] = ['%(app_label)s.view_%(model_name)s']
        self.perms_map['PATCH'] = ['%(app_label)s.change_%(model_name)s']

        return super(XFormPermissions, self).__init__(*args, **kwargs)

    def has_permission(self, request, view):
        owner = view.kwargs.get('owner')
        is_authenticated = request and request.user.is_authenticated()

        if 'pk' in view.kwargs:

            # Allow anonymous users to access shared data
            if request.method == 'GET' and view.action in ('list', 'retrieve'):
                pk = view.kwargs.get('pk')
                xform = get_object_or_404(XForm, pk=pk)
                if xform.shared_data:
                    return True

            check_inherit_permission_from_project(view.kwargs.get('pk'),
                                                  request.user)

        if is_authenticated and view.action == 'create':
            owner = owner or request.user.username

            return request.user.has_perm(CAN_ADD_XFORM_TO_PROFILE,
                                         get_user_profile_or_none(owner))

        return super(XFormPermissions, self).has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        # Allow anonymous users to access shared data
        if request.method == 'GET' and view.action in ('list', 'retrieve'):
            pk = view.kwargs.get('pk')
            xform = get_object_or_404(XForm, pk=pk)
            if xform.shared_data:
                return True

        if request.method == 'DELETE' and view.action == 'labels':
            user = request.user
            return user.has_perms([CAN_CHANGE_XFORM], obj)

        if request.method in ['PATCH', 'DELETE'] \
                and view.action.endswith('validation_status'):
            user = request.user
            return user.has_perms([CAN_VALIDATE_XFORM], obj)

        return super(XFormPermissions, self).has_object_permission(
            request, view, obj)


class XFormDataPermissions(XFormPermissions):

    # TODO: move other data-specific logic out of `XFormPermissions` and into
    # this class

    def __init__(self, *args, **kwargs):
        super(XFormDataPermissions, self).__init__(*args, **kwargs)
        # Those who can edit submissions can also delete them, following the
        # behavior of `onadata.apps.main.views.delete_data`
        self.perms_map['DELETE'] = ['%(app_label)s.' + CAN_CHANGE_XFORM]


class UserProfilePermissions(DjangoObjectPermissions):

    authenticated_users_only = False

    def has_permission(self, request, view):
        # allow anonymous users to create new profiles
        if request.user.is_anonymous() and view.action == 'create':
            return True

        return \
            super(UserProfilePermissions, self).has_permission(request, view)


class ProjectPermissions(DjangoObjectPermissions):

    authenticated_users_only = False

    def has_permission(self, request, view):
        # allow anonymous to view public projects
        if request.user.is_anonymous() and view.action == 'list':
            return True

        if not request.user.is_anonymous() and view.action == 'star':
            return True

        return \
            super(ProjectPermissions, self).has_permission(request, view)


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
        # It doesn't work with DRF 3 because the model class is retrived
        # using get_queryset. We should replace this hack by something
        # cleaner, but that would need to rework the entire permissions system
        # so instead, we are keeping the spirit of the original hack
        # by temporarly patching get_queryset.

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
    def has_object_permission(self, request, view, obj):
        view.model = XForm

        return super(AttachmentObjectPermissions, self).has_object_permission(
            request, view, obj.instance.xform)


class ConnectViewsetPermissions(IsAuthenticated):

    def has_permission(self, request, view):
        if view.action == 'reset':
            return True

        return super(ConnectViewsetPermissions, self)\
            .has_permission(request, view)

__permissions__ = [DjangoObjectPermissions, IsAuthenticated]
