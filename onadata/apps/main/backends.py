# coding: utf-8
from __future__ import unicode_literals, print_function, division, absolute_import

from django.contrib.auth.models import User
from django.contrib.auth.backends import ModelBackend as DjangoModelBackend


class ModelBackend(DjangoModelBackend):
    def authenticate(self, username=None, password=None):
        """Username is case insensitive."""
        try:
            user = User.objects.get(username__iexact=username)
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            return None
