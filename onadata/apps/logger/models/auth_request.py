# coding: utf-8
from datetime import timedelta
from typing import Union

from django.conf import settings
from django.contrib.auth.models import User
from django.core.signing import Signer
from django.db import models
from django.db.models import Q, F, Func
from django.utils import timezone


class OneTimeAuthRequest(models.Model):

    HEADER = 'X-KOBOCAT-OTAR-TOKEN'
    DEFAULT_TTL = 60  # Number of seconds before a token expires

    user = models.ForeignKey(
        User, related_name='authenticated_requests', on_delete=models.CASCADE
    )
    token = models.CharField(max_length=50)
    date_created = models.DateTimeField(default=timezone.now)
    ttl = models.IntegerField(default=DEFAULT_TTL)
    method = models.CharField(max_length=6)
    used = models.BooleanField(default=False)

    class Meta:
        unique_together = ('token', 'used')

    @classmethod
    def grant_access(
        cls,
        request: 'rest_framework.request.Request',
        use_referrer: bool = True,
    ):
        token = cls.is_signed_request(request, use_referrer)
        if token is None:
            # No token is detected, the authentication should be
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

            # clean-up expired or already used tokens
            OneTimeAuthRequest.objects.filter(
                Q(
                    date_created__lt=Func(
                        F('ttl'),
                        template="now() - INTERVAL '1 seconds' * %(expressions)s",
                    ),
                    used=False,
                )
                | Q(used=True),
                user=user,
            ).delete()

        return granted

    @classmethod
    def is_signed_request(
        cls,
        request: 'rest_framework.request.Request',
        use_referrer: bool = False,
    ) -> Union[str, None]:
        """
        Search for a OneTimeAuthRequest token in the request headers.
        If there is a match, it is returned. Otherwise, it returns `None`.

        If `use_referrer` is `True`, the comparison is also made on the
        HTTP referrer.
        """
        try:
            token = request.headers[cls.HEADER]
        except KeyError:
            if not use_referrer:
                return None
        else:
            return token

        try:
            referrer = request.META['HTTP_REFERER']
        except KeyError:
            return None
        else:
            # There is no reason that the referrer could be something else
            # than Enketo Express edit URL.
            edit_url = f'{settings.ENKETO_URL}/edit'
            if not referrer.startswith(edit_url):
                return None

            parts = Signer().sign(referrer).split(':')
            return parts[-1]
