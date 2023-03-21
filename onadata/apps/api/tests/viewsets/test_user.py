# coding: utf-8
from onadata.apps.api.viewsets.user import UserViewSet
from .test_abstract_viewset import TestAbstractViewSet


class TestUserViewSet(TestAbstractViewSet):

    def setUp(self):
        self.retrieve_view = UserViewSet.as_view({
            'get': 'retrieve',
            'delete': 'destroy'
        })

        self.list_view = UserViewSet.as_view({
            'get': 'list'
        })

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
        self.alice = alice_profile.user
        self.admin = admin_profile.user

    def test_no_access_to_users_list(self):
        pass

    def test_no_access_to_user_detail(self):
        pass

    def test_superuser_cannot_access_user_detail(self):
        pass

    def test_superuser_cannot_delete_user(self):
        pass

    def test_cannot_access_myself_detail(self):
        pass

    def test_cannot_delete_myself(self):
        pass

    def test_service_account_cannot_access_user_detail(self):
        pass

    def test_service_account_can_delete_user(self):
        pass
