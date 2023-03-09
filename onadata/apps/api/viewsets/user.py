from django.contrib.auth import get_user_model
from rest_framework import viewsets, mixins, renderers

from ..permissions import UserDeletePermission


class UserViewSet(mixins.DestroyModelMixin, viewsets.GenericViewSet):

    lookup_field = 'username'
    queryset = get_user_model().objects.all()
    permission_classes = [UserDeletePermission]
    renderer_classes = (renderers.JSONRenderer,)
