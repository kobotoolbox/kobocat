# coding: utf-8
from django.test import override_settings
from django.test.client import Client
from django.urls import reverse
from requests.auth import HTTPDigestAuth

from onadata.apps.main.tests.test_base import TestBase


class TestAuthBase(TestBase):

    def setUp(self):
        TestBase.setUp(self)
        self._create_user_and_login(username='bob', password='bob')
        self._publish_transportation_form()
        self.api_url = reverse('data-list', kwargs={
            'pk': self.xform.pk,
            'format': 'json'
        })
        print('self.api_url', self.api_url, flush=True)
        self._logout()


class TestBasicHttpAuthentication(TestAuthBase):

    def test_http_auth(self):
        response = self.client.get(self.api_url)
        self.assertEqual(response.status_code, 404)
        # headers with invalid user/pass
        response = self.client.get(self.api_url,
                                   **self._set_auth_headers('x', 'y'))
        self.assertEqual(response.status_code, 401)

        # headers with valid user/pass
        client = Client()
        response = client.get(
            self.api_url, **self._set_auth_headers('bob', 'bob')
        )
        self.assertEqual(response.status_code, 200)

    def test_http_auth_shared_data(self):
        self.xform.shared_data = True
        self.xform.save()
        response = self.anon.get(self.api_url)
        self.assertEqual(response.status_code, 200)
        response = self.client.get(self.api_url)
        self.assertEqual(response.status_code, 200)

    def test_http_auth_failed_with_mfa_active(self):
        # headers with valid user/pass
        response = self.client.get(self.api_url,
                                   **self._set_auth_headers('bob', 'bob'))
        self.assertEqual(response.status_code, 200)

        # Activate MFA
        self.user.profile.is_mfa_active = True
        self.user.profile.save()
        response = self.client.get(self.api_url,
                                   **self._set_auth_headers('bob', 'bob'))
        self.assertEqual(response.status_code, 401)

    def test_http_auth_with_mfa_active_with_exception(self):
        # Activate MFA
        self.user.profile.is_mfa_active = True
        self.user.profile.save()
        response = self.client.get(self.api_url,
                                   **self._set_auth_headers('bob', 'bob'))
        self.assertEqual(response.status_code, 401)

        # Allow Basic Auth with MFA
        with override_settings(MFA_SUPPORTED_AUTH_CLASSES=[
            'onadata.libs.authentication.HttpsOnlyBasicAuthentication',
        ]):
            response = self.client.get(self.api_url,
                                       **self._set_auth_headers('bob', 'bob'))
            self.assertEqual(response.status_code, 200)


class TestDigestAuthentication(TestAuthBase):

    def setUp(self):
        super().setUp()
        # Data endpoint does not support Digest.
        # Let's test it against the XForm list
        self.api_url = reverse('data-list', kwargs={'format': 'json'})

    def test_digest_auth_failed_with_mfa_active(self):
        # headers with valid user/pass
        digest_client = self._get_authenticated_client(
            self.api_url, 'bob', 'bob'
        )
        response = digest_client.get(self.api_url)
        self.assertEqual(response.status_code, 200)

        # Activate MFA
        self.user.profile.is_mfa_active = True
        self.user.profile.save()
        digest_client = self._get_authenticated_client(
            self.api_url, 'bob', 'bob'
        )
        response = digest_client.get(self.api_url)
        self.assertEqual(response.status_code, 401)

    def test_digest_auth_with_mfa_active_with_exception(self):
        # Activate MFA
        self.user.profile.is_mfa_active = True
        self.user.profile.save()
        digest_client = self._get_authenticated_client(
            self.api_url, 'bob', 'bob'
        )
        response = digest_client.get(self.api_url)
        self.assertEqual(response.status_code, 401)

        # Allow Basic Auth with MFA
        with override_settings(MFA_SUPPORTED_AUTH_CLASSES=[
            'onadata.libs.authentication.DigestAuthentication',
        ]):
            digest_client = self._get_authenticated_client(
                self.api_url, 'bob', 'bob'
            )
            response = digest_client.get(self.api_url)
            self.assertEqual(response.status_code, 200)


class TestTokenAuthentication(TestAuthBase):

    def _set_auth_headers(self, token):
        return {
            'HTTP_AUTHORIZATION': f'Token {token}'
        }

    def test_token_auth_failed_with_mfa_active(self):
        # headers with valid user/pass
        response = self.client.get(self.api_url,
                                   **self._set_auth_headers(self.user.auth_token))
        self.assertEqual(response.status_code, 200)

        # Activate MFA, token auth is allowed with MFA by default
        self.user.profile.is_mfa_active = True
        self.user.profile.save()
        response = self.client.get(self.api_url,
                                   **self._set_auth_headers(self.user.auth_token))
        self.assertEqual(response.status_code, 200)

    def test_token_auth_with_mfa_active_with_exception(self):
        # Activate MFA
        self.user.profile.is_mfa_active = True
        self.user.profile.save()

        # Forbid token auth with MFA (it's allowed by default)
        with override_settings(MFA_SUPPORTED_AUTH_CLASSES=[]):
            response = self.client.get(self.api_url,
                                       **self._set_auth_headers(self.user.auth_token))
            self.assertEqual(response.status_code, 401)

        # Default settings, allow token Auth with MFA
        response = self.client.get(self.api_url,
                                   **self._set_auth_headers(self.user.auth_token))
        self.assertEqual(response.status_code, 200)
