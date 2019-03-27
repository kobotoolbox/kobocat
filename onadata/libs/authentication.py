from django.utils.translation import ugettext as _
from django_digest import HttpDigestAuthenticator
from rest_framework.authentication import (
    BaseAuthentication, get_authorization_header,
    BasicAuthentication)
from rest_framework.exceptions import AuthenticationFailed


class DigestAuthentication(BaseAuthentication):
    def __init__(self):
        self.authenticator = HttpDigestAuthenticator()

    def authenticate(self, request):

        auth = get_authorization_header(request).split()

        if not auth or auth[0].lower() != b'digest':
            return None
        if self.authenticator.authenticate(request):
            return request.user, None
        else:
            raise AuthenticationFailed(
                _(u"Invalid username/password"))

    def authenticate_header(self, request):
        response = self.authenticator.build_challenge_response()

        return response['WWW-Authenticate']


class HttpsOnlyBasicAuthentication(BasicAuthentication):
    def authenticate(self, request):
        # The parent class can discern whether basic authentication is even
        # being attempted; if it isn't, we need to gracefully defer to other
        # authenticators
        user_auth = super(HttpsOnlyBasicAuthentication, self).authenticate(
            request)
        if user_auth is not None and not request.is_secure():
            # Scold the user if they provided correct credentials for basic
            # auth but didn't use HTTPS
            raise AuthenticationFailed(_(
                u'Using basic authentication without HTTPS transmits '
                u'credentials in clear text! You MUST connect via HTTPS '
                u'to use basic authentication.'
            ))
        return user_auth
