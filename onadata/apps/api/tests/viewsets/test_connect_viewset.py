# coding: utf-8
from __future__ import unicode_literals, print_function, division, absolute_import

from django_digest.test import DigestAuth, BasicAuth
from rest_framework import authentication

from onadata.apps.api.tests.viewsets.test_abstract_viewset import \
    TestAbstractViewSet
from onadata.apps.api.viewsets.connect_viewset import ConnectViewSet
from onadata.libs.authentication import DigestAuthentication


class TestConnectViewSet(TestAbstractViewSet):
    def setUp(self):
        super(self.__class__, self).setUp()
        self.view = ConnectViewSet.as_view({
            "get": "list",
        })
        self.data = {
            'id': 1,
            'username': 'bob',
            'name': 'Bob',
            'email': 'bob@columbia.edu',
            'city': 'Bobville',
            'country': 'US',
            'organization': 'Bob Inc.',
            'website': 'bob.com',
            'twitter': 'boberama',
            'gravatar': self.user.profile.gravatar,
            'require_auth': False,
            'api_token': self.user.auth_token.key,
            'temp_token': self.client.session.session_key,
            'metadata': {},
        }

    def test_get_profile(self):
        request = self.factory.get('/', **self.extra)
        request.session = self.client.session

        response = self.view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, self.data)

    def test_user_list_with_digest(self):
        view = ConnectViewSet.as_view(
            {'get': 'list'},
            authentication_classes=(DigestAuthentication,))
        request = self.factory.head('/')

        auth = DigestAuth('bob', 'bob')
        response = view(request)
        self.assertTrue(response.has_header('WWW-Authenticate'))
        self.assertTrue(
            response['WWW-Authenticate'].startswith('Digest nonce='))
        request = self.factory.get('/')
        request.META.update(auth(request.META, response))
        request.session = self.client.session

        response = view(request)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data['detail'],
                         "Invalid username/password")
        auth = DigestAuth('bob', 'bobbob')
        request.META.update(auth(request.META, response))
        request.session = self.client.session

        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, self.data)

    def test_user_list_with_basic_and_digest(self):
        view = ConnectViewSet.as_view(
            {'get': 'list'},
            authentication_classes=(
                DigestAuthentication,
                authentication.BasicAuthentication
            ))
        request = self.factory.get('/')
        auth = BasicAuth('bob', 'bob')
        request.META.update(auth(request.META))
        request.session = self.client.session

        response = view(request)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data['detail'],
                         "Invalid username/password.")
        auth = BasicAuth('bob', 'bobbob')

        # redo the request
        request = self.factory.get('/')
        request.META.update(auth(request.META))
        request.session = self.client.session

        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, self.data)
