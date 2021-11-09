# coding: utf-8
from typing import Optional, Union
from urllib.parse import urlparse, parse_qs

from django.conf import settings
from django.contrib.auth.models import User
from django.core.signing import Signer
from django.db import models
from django.utils import timezone


class OneTimeAuthToken(models.Model):

    HEADER = 'X-KOBOCAT-OTA-TOKEN'
    QS_PARAM = 'kc_ota_token'

    user = models.ForeignKey(
        User, related_name='authenticated_requests', on_delete=models.CASCADE
    )
    token = models.CharField(max_length=50)
    expiration_time = models.DateTimeField()
    method = models.CharField(max_length=6)
    request_identifier = models.CharField(max_length=1000, null=True)

    class Meta:
        unique_together = ('user', 'token', 'method')

    @classmethod
    def grant_access(
        cls,
        request: Union[
            'rest_framework.request.Request',
            'django.http.HttpRequest'
        ],
        use_referrer: bool = False,
        instance: Optional['onadata.apps.logger.models.Instance'] = None,
    ):
        token, validate_url = cls.is_signed_request(
            request, use_referrer, instance
        )
        if token is None:
            # No token is detected, the authentication should be
            # delegated to other mechanisms present in permission classes
            return None

        user = request.user
        # Anonymous cannot have a one time authentication token
        if user.is_anonymous:
            return None

        token_attrs = {
            'user': user,
            'token': token,
            'method': request.method,
        }

        if validate_url:
            url = request.build_absolute_uri().replace(
                f'&{cls.QS_PARAM}={token}', ''
            )
            token_attrs['request_identifier'] = url

        try:
            auth_token = cls.objects.get(**token_attrs)
        except OneTimeAuthToken.DoesNotExist:
            return False

        granted = timezone.now() <= auth_token.expiration_time

        # clean-up expired or already used tokens
        OneTimeAuthToken.objects.filter(
            expiration_time__lt=timezone.now(),
            user=user,
        ).delete()

        return granted

    @classmethod
    def is_signed_request(
        cls,
        request: Union[
            'rest_framework.request.Request',
            'django.http.HttpRequest'
        ],
        use_referrer: bool = False,
        instance: Optional['onadata.apps.logger.models.Instance'] = None,
    ) -> tuple:
        """
        Search for a OneTimeAuthToken in the request headers, the querystring or
        the HTTP referrer (if `use_referrer` is `True`).

        It returns a tuple. The first element is the token if a match has been
        found. Otherwise, it is `None`. The second element is a boolean which
        represents whether the validation of the URL must enforced.
        When the comparison is made on the HTTP referrer, `instance` must be
        provided. The referrer must include an `instance_id` query parameter
        that matches `instance.uuid`.
        """
        try:
            token = request.headers[cls.HEADER]
        except KeyError:
            try:
                token = request.GET[cls.QS_PARAM]
            except KeyError:
                if not use_referrer:
                    return None, False
            else:
                return token, True
        else:
            return token, False

        if use_referrer and not instance:
            raise TypeError(  # I win!!!
                '`instance` must be provided when `use_referrer = True`'
            )

        try:
            referrer = request.META['HTTP_REFERER']
        except KeyError:
            return None, False
        else:
            # There is no reason that the referrer could be something else
            # than Enketo Express edit URL.
            edit_url = f'{settings.ENKETO_URL}/edit'
            if not referrer.startswith(edit_url):
                return None, False

            # When using partial permissions, deny access if the UUID in the
            # referrer URL does not match the UUID of the submission being
            # edited
            referrer_qs = parse_qs(urlparse(referrer).query)
            try:
                referrer_uuid = referrer_qs['instance_id'][0]
            except (IndexError, KeyError):
                return None, False
            else:
                if referrer_uuid != instance.uuid:
                    return None, False

            parts = Signer().sign(referrer).split(':')
            return parts[-1], False
