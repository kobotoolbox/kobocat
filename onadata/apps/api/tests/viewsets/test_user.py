# coding: utf-8
import pytest
from django.conf import settings
from django.urls.exceptions import NoReverseMatch
from rest_framework import status
from rest_framework.reverse import reverse

from kobo_service_account.utils import get_request_headers
from .test_abstract_viewset import TestAbstractViewSet


class TestUserViewSet(TestAbstractViewSet):

    def setUp(self):
        alice_profile_data = {
            'username': 'alice',
            'email': 'alice@kobotoolbox.org',
            'password1': 'alice',
            'password2': 'alice',
            'name': 'Alice',
            'city': 'AliceTown',
            'country': 'CA',
            'organization': 'Alice Inc.',
            'home_page': 'alice.com',
            'twitter': 'alicetwitter'
        }

        admin_profile_data = {
            'username': 'admin',
            'email': 'admin@kobotoolbox.org',
            'password1': 'admin',
            'password2': 'admin',
            'name': 'Administrator',
            'city': 'AdminTown',
            'country': 'CA',
            'organization': 'Admin Inc.',
            'home_page': 'admin.com',
            'twitter': 'admintwitter'
        }

        alice_profile = self._create_user_profile(alice_profile_data)
        admin_profile = self._create_user_profile(admin_profile_data)
        bob_profile = self._create_user_profile(self.default_profile_data)
        self.alice = alice_profile.user
        self.admin = admin_profile.user
        self.bob = bob_profile.user

    def test_no_access_to_users_list(self):
        # anonymous user
        pattern = (
            r"^Reverse for 'user-list' not found. 'user-list' is not a valid view "
            "function or pattern name.$"
        )
        with pytest.raises(NoReverseMatch, match=pattern) as e:
            reverse('user-list')

    def test_no_access_to_user_detail(self):
        # anonymous user
        self.client.logout()
        url = reverse('user-detail', args=(self.alice.username,))
        response = self.client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

        # bob
        self.client.login(username='bob', password='bobbob')
        url = reverse('user-detail', args=(self.alice.username,))
        response = self.client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_superuser_cannot_access_user_detail(self):
        self.client.login(username='admin', password='admin')
        url = reverse('user-detail', args=(self.alice.username,))
        response = self.client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_superuser_cannot_delete_user(self):
        self.client.login(username='admin', password='admin')
        url = reverse('user-detail', args=(self.alice.username,))
        response = self.client.delete(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_cannot_access_myself_detail(self):
        self.client.login(username='alice', password='alice')
        url = reverse('user-detail', args=(self.alice.username,))
        response = self.client.delete(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_cannot_delete_myself(self):
        self.client.login(username='alice', password='alice')
        url = reverse('user-detail', args=(self.alice.username,))
        response = self.client.delete(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_service_account_cannot_access_user_detail(self):
        self.client.logout()
        url = reverse('user-detail', args=(self.alice.username,))
        service_account_meta = self.get_meta_from_headers(
            get_request_headers(self.alice.username)
        )
        service_account_meta['HTTP_HOST'] = settings.TEST_HTTP_HOST
        response = self.client.get(url, **service_account_meta)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_service_account_can_delete_user(self):
        self.client.logout()
        url = reverse('user-detail', args=(self.alice.username,))
        service_account_meta = self.get_meta_from_headers(
            get_request_headers(self.alice.username)
        )
        service_account_meta['HTTP_HOST'] = settings.TEST_HTTP_HOST
        response = self.client.delete(url, **service_account_meta)
        assert response.status_code == status.HTTP_204_NO_CONTENT
