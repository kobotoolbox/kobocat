import unittest

from django.contrib.auth.models import User

from test_base import TestBase
from test_user_profile import TestUserProfile


class TestUserLogin(TestBase):

    def test_any_case_login_ok(self):
        username = 'bob'
        password = 'bobbob'
        # kobocat lo
        self._create_user(username, password)
        # kobocat login are now case sensitive so you must lowercase BOB
        self._login('bob', password)

    @unittest.skip('Kobocat is now case sensitive')
    def test_username_is_made_lower_case(self):
        username = 'ROBERT'
        password = 'bobbob'
        self._create_user(username, password)
        self._login('robert', password)

    def test_redirect_if_logged_in(self):
        self._create_user_and_login()
        response = self.client.get('')
        self.assertEqual(response.status_code, 302)


class TestUserReservedNames(TestUserProfile):

    @unittest.skip('This feature is now deported on the API')
    def test_disallow_reserved_names(self):
        username = 'forms'
        count = User.objects.count()
        self._login_user_and_profile({'username': username})
        self.assertEqual(len(User.objects.all()), count)
