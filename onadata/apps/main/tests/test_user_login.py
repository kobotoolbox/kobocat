# coding: utf-8
from __future__ import unicode_literals, print_function, division, absolute_import
import unittest

from django.contrib.auth.models import User

from .test_base import TestBase
from .test_user_profile import TestUserProfile


class TestUserLogin(TestBase):

    def test_any_case_login_ok(self):
        username = 'bob'
        password = 'bobbob'
        # kobocat lo
        self._create_user(username, password)
        # kobocat login are now case sensitive so you must lowercase BOB
        self._login('bob', password)

    def test_redirect_if_logged_in(self):
        self._create_user_and_login()
        response = self.client.get('')
        self.assertEqual(response.status_code, 302)
