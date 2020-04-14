# coding: utf-8
from __future__ import unicode_literals, print_function, division, absolute_import

import json

from django.contrib.auth.models import User
from rest_framework import status

from onadata.apps.api.tests.viewsets.test_abstract_viewset import \
    TestAbstractViewSet
from onadata.apps.api.viewsets.user_profile_viewset import UserProfileViewSet
from onadata.apps.main.models import UserProfile
from onadata.libs.serializers.user_profile_serializer import (
    _get_first_last_names
)


def _profile_data():
    return {
        'username': 'deno',
        'name': 'Dennis',
        'email': 'deno@columbia.edu',
        'city': 'Denoville',
        'country': 'US',
        'organization': 'Dono Inc.',
        'website': 'deno.com',
        'twitter': 'denoerama',
        'require_auth': False,
        'password': 'denodeno',
    }


class TestUserProfileViewSet(TestAbstractViewSet):

    def setUp(self):
        super(self.__class__, self).setUp()
        self.view = UserProfileViewSet.as_view({
            'get': 'list',
            'post': 'create',
            'patch': 'partial_update'
        })

    def test_profiles_list(self):
        request = self.factory.get('/', **self.extra)
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Anonymous User
        request = self.factory.get('/')
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_profiles_get(self):
        """Test get user profile"""
        view = UserProfileViewSet.as_view({
            'get': 'retrieve'
        })
        request = self.factory.get('/', **self.extra)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data, {'detail': 'Expected URL keyword argument `user`.'})

        # by username
        response = view(request, user='bob')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, self.user_profile_data())

        # by pk
        response = view(request, user=self.user.pk)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, self.user_profile_data())

    def test_profiles_get_anon(self):
        view = UserProfileViewSet.as_view({
            'get': 'retrieve'
        })
        request = self.factory.get('/')
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        request = self.factory.get('/')
        response = view(request, user='bob')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_profile_create(self):
        request = self.factory.get('/', **self.extra)
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        data = _profile_data()
        request = self.factory.post(
            '/api/v1/profiles', data=json.dumps(data),
            content_type="application/json", **self.extra)
        response = self.view(request)
        self.assertEqual(response.status_code, 201)
        del data['password']
        profile = UserProfile.objects.get(user__username=data['username'])
        data['id'] = profile.user.pk
        data['gravatar'] = profile.gravatar
        data['url'] = 'http://testserver/api/v1/profiles/deno'
        data['user'] = 'http://testserver/api/v1/users/deno'
        data['metadata'] = {}
        self.assertEqual(response.data, data)

        user = User.objects.get(username='deno')
        self.assertTrue(user.is_active)

    def test_profile_create_anon(self):
        data = _profile_data()
        request = self.factory.post(
            '/api/v1/profiles', data=json.dumps(data),
            content_type="application/json")
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_profile_create_missing_name_field(self):
        data = _profile_data()
        del data['name']
        request = self.factory.post(
            '/api/v1/profiles', data=json.dumps(data),
            content_type="application/json",
            HTTP_ACCEPT='application/javascript',  # get JSONP response
            **self.extra)
        response = self.view(request)
        response.render()

        self.assertEqual(response.data, {"name": ["This field is required."]})

    def test_split_long_name_to_first_name_and_last_name(self):
        name = "(CPLTGL) Centre Pour la Promotion de la Liberte D'Expression "\
            "et de la Tolerance Dans La Region de"
        first_name, last_name = _get_first_last_names(name)
        self.assertEqual(first_name, "(CPLTGL) Centre Pour la Promot")
        self.assertEqual(last_name, "ion de la Liberte D'Expression")

    def test_partial_updates(self):
        self.assertEqual(self.user.profile.country, 'US')

        country = 'KE'
        data = {'country': country}
        request = self.factory.patch('/', data=data, **self.extra)
        response = self.view(request, user=self.user.username)
        profile = UserProfile.objects.get(user=self.user)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(profile.country, country)

    def test_profile_create_mixed_case(self):
        data = _profile_data()

        request = self.factory.post(
            '/api/v1/profiles', data=json.dumps(data),
            content_type="application/json",
            HTTP_ACCEPT="application/javascript",  # get JSONP response
            **self.extra)
        response = self.view(request)

        del data['password']
        profile = UserProfile.objects.get(
            user__username=data['username'].lower())

        data['id'] = profile.user.pk
        data['gravatar'] = unicode(profile.gravatar)
        data['url'] = 'http://testserver/api/v1/profiles/deno'
        data['user'] = 'http://testserver/api/v1/users/deno'
        data['username'] = 'deno'
        data['metadata'] = {}

        data['username'] = 'deno'
        request = self.factory.post(
            '/api/v1/profiles', data=json.dumps(data),
            content_type="application/json",
            HTTP_ACCEPT='application/javascript',
            **self.extra)
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        msg = "%s already exists" % data['username']
        self.assertIn(msg, response.data['username'][0])

    def test_change_password(self):
        view = UserProfileViewSet.as_view(
            {'post': 'change_password'})
        current_password = "bobbob"
        new_password = "bobbob1"
        post_data = {'current_password': current_password,
                     'new_password': new_password}

        request = self.factory.post('/', data=post_data, **self.extra)
        response = view(request, user='bob')
        user = User.objects.get(username__iexact=self.user.username)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(user.check_password(new_password))

    def test_change_password_wrong_current_password(self):
        view = UserProfileViewSet.as_view(
            {'post': 'change_password'})
        current_password = "wrong_pass"
        new_password = "bobbob1"
        post_data = {'current_password': current_password,
                     'new_password': new_password}

        request = self.factory.post('/', data=post_data, **self.extra)
        response = view(request, user='bob')
        user = User.objects.get(username__iexact=self.user.username)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(user.check_password(new_password))
