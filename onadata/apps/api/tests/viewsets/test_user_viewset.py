# coding: utf-8
from collections import OrderedDict

from rest_framework import status

from onadata.apps.api.tests.viewsets.test_abstract_viewset import\
    TestAbstractViewSet
from onadata.apps.api.viewsets.user_viewset import UserViewSet


class TestUserViewSet(TestAbstractViewSet):
    def setUp(self):
        super(self.__class__, self).setUp()
        self.data = OrderedDict([
            ('id', self.user.pk),
            ('username', u'bob'),
            ('first_name', u'Bob'),
            ('last_name', u''),
            ('url', u'http://testserver/api/v1/users/bob')
        ])

    def test_user_get(self):
        """Test authenticated user can access user info"""
        alice_data = {'username': 'alice', 'email': 'alice@localhost.com'}
        self._create_user_profile(alice_data)

        request = self.factory.get('/', **self.extra)

        # users list
        view = UserViewSet.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # user with username bob
        view = UserViewSet.as_view({'get': 'retrieve'})
        response = view(request, username='bob')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, self.data)

        # user with username alice
        view = UserViewSet.as_view({'get': 'retrieve'})
        response = view(request, username='alice')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_anon(self):
        """Test anonymous user cannot access user info"""
        request = self.factory.get('/')

        # users list endpoint
        view = UserViewSet.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # user with username bob
        view = UserViewSet.as_view({'get': 'retrieve'})
        response = view(request, username='bob')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Test with primary key
        response = view(request, username=self.user.pk)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
