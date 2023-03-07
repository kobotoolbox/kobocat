from django.contrib.auth import get_user_model
from rest_framework import viewsets, mixins, renderers


class UserViewSet(mixins.DestroyModelMixin, viewsets.GenericViewSet):

    lookup_field = 'username'
    queryset = get_user_model().objects.all()
    permission_classes = []
    renderer_classes = (renderers.JSONRenderer,)
