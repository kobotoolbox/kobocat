# coding: utf-8
from django.conf import settings
from django.utils.translation import ugettext as _
from django.http import HttpResponse
from django_digest import HttpDigestAuthenticator
from rest_framework.authentication import (
    BaseAuthentication,
    BasicAuthentication,
    get_authorization_header,
)
from rest_framework.exceptions import AuthenticationFailed


def digest_authentication(request):
    authenticator = DigestAuthentication()
    try:
        authentication = authenticator.authenticate(request)
    except AuthenticationFailed as e:
        return HttpResponse(
            str(e),
            content_type=request.headers['content-type'],
            status=AuthenticationFailed.status_code
        )
    else:
        if not authentication:
            return authenticator.build_challenge_response()


class DigestAuthentication(BaseAuthentication):
    def __init__(self):
        self.authenticator = HttpDigestAuthenticator()

    def authenticate(self, request):

        auth = get_authorization_header(request).split()

        if not auth or auth[0].lower() != b'digest':
            return None

        if self.authenticator.authenticate(request):

            # If user provided correct credentials but their account is
            # disabled, return a 401
            if not request.user.is_active:
                raise AuthenticationFailed()

            return request.user, None
        else:
            raise AuthenticationFailed(_('Invalid username/password'))

    def authenticate_header(self, request):
        response = self.build_challenge_response()
        return response['WWW-Authenticate']

    def build_challenge_response(self):
        return self.authenticator.build_challenge_response()


class HttpsOnlyBasicAuthentication(BasicAuthentication):

    def authenticate(self, request):
        # The parent class can discern whether basic authentication is even
        # being attempted; if it isn't, we need to gracefully defer to other
        # authenticators
        user_auth = super().authenticate(
            request)
        if settings.TESTING_MODE is False and \
                user_auth is not None and not request.is_secure():
            # Scold the user if they provided correct credentials for basic
            # auth but didn't use HTTPS
            raise AuthenticationFailed(_(
                'Using basic authentication without HTTPS transmits '
                'credentials in clear text! You MUST connect via HTTPS '
                'to use basic authentication.'
            ))
        return user_auth
