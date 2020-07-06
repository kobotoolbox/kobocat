from django.contrib.auth import authenticate
from django.contrib.auth.middleware import RemoteUserMiddleware
from rest_framework.authentication import BaseAuthentication


class QedAuthMiddleware(RemoteUserMiddleware):
    header = 'HTTP_X_AUTH_USERNAME'


# TODO(m1): inherit from https://github.com/encode/django-rest-framework/pull/5306
# TODO(m1): when the DRF version with that class lands
class QedRemoteUserAuth(BaseAuthentication):
    """
    REMOTE_USER authentication.

    To use this, set up your web server to perform authentication, which will
    set the REMOTE_USER environment variable. You will need to have
    'django.contrib.auth.backends.RemoteUserBackend in your
    AUTHENTICATION_BACKENDS setting
    """

    # Name of request header to grab username from.  This will be the key as
    # used in the request.META dictionary, i.e. the normalization of headers to
    # all uppercase and the addition of "HTTP_" prefix apply.
    header = 'HTTP_X_AUTH_USERNAME'

    def authenticate(self, request):
        user = authenticate(remote_user=request.META.get(self.header))
        if user and user.is_active:
            return (user, None)
