# coding: utf-8
from datetime import timedelta

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class OneTimeAuthRequest(models.Model):

    HEADER = 'X-KOBOCAT-OTAR-TOKEN'
    DEFAULT_TTL = 60  # Number of seconds before a token expires

    user = models.ForeignKey(
        User, related_name='authenticated_requests', on_delete=models.CASCADE
    )
    token = models.CharField(max_length=50, unique=True)
    date_created = models.DateTimeField(default=timezone.now)
    ttl = models.IntegerField(default=DEFAULT_TTL)
    method = models.CharField(max_length=6)
    used = models.BooleanField(default=False)

    @classmethod
    def grant_access(cls, request):
        token = cls.is_signed_request(request)
        if token is None:
            # No token is present in the header, the authentication should be
            # delegated to other mechanisms present in permission classes
            return None

        granted = False
        user = request.user
        try:
            auth_request = cls.objects.get(
                user=user, token=token, method=request.method, used=False
            )
        except OneTimeAuthRequest.DoesNotExist:
            pass
        else:
            expiry = (
                auth_request.date_created
                + timedelta(seconds=auth_request.ttl)
            )
            granted = timezone.now() < expiry

            # void token
            auth_request.used = True
            auth_request.save()

            # clean-up expired tokens
            time_threshold = timezone.now() - timedelta(seconds=cls.DEFAULT_TTL)
            OneTimeAuthRequest.objects.filter(
                user=user, date_created__lt=time_threshold
            ).delete()

        return granted

    @classmethod
    def is_signed_request(cls, request):
        try:
            token = request.headers[cls.HEADER]
        except KeyError:
            return None

        return token
