from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from django.conf import settings

import requests
import logging
import python_digest

class VeritreeAuth(ModelBackend):
    def authenticate(self, request, username=None, password=None):
        try:
            digest_response = python_digest.parse_digest_credentials(
                request.META['HTTP_AUTHORIZATION'])
            if digest_response:
                logger = logging.getLogger("console_logger")
                logger.error(
                    " '%s'" % digest_response.username, exc_info=True)
                username = digest_response.username
                logger.error(
                    " '%s'" % digest_response.password, exc_info=True)
                password = digest_response.password
        except:
            pass

       

        if username and password:
            try:
                token_response = requests.post('{koboform_url}/token/'.format(koboform_url=settings.KOBOFORM_URL), data={'username': username, 'password': password })
                if token_response.status_code >= 200 and token_response.status_code < 300:
                    user_lookup_response = requests.get('{koboform_url}/me/'.format(koboform_url=settings.KOBOFORM_URL), headers={'Authorization': 'Token {}'.format(token_response.json()['token'])})
                    if user_lookup_response.status_code >= 200 and token_response.status_code < 300:
                        username = user_lookup_response.json()['username']
                        try:
                            return User.objects.get(username=username)
                        except User.DoesNotExist:
                            return None
            except:
                # Don't crash, although should handle this better
                pass
        return None