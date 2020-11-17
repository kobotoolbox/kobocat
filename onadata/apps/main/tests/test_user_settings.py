# coding: utf-8
from __future__ import unicode_literals, print_function, division, absolute_import
import unittest
from django.core.urlresolvers import reverse

from onadata.apps.main.models import UserProfile
from onadata.apps.main.views import profile_settings
from .test_base import TestBase


class TestUserSettings(TestBase):

    def setUp(self):
        TestBase.setUp(self)
        self.settings_url = reverse(
            profile_settings, kwargs={'username': self.user.username})

    def test_render_user_settings(self):
        response = self.client.get(self.settings_url)
        self.assertEqual(response.status_code, 200)

    def test_update_user_settings(self):
        self.assertFalse(self.user.profile.require_auth)
        post_data = {
            'require_auth': True,
        }
        response = self.client.post(self.settings_url, post_data)
        self.assertEqual(response.status_code, 302)
        self.user.profile.refresh_from_db()
        self.assertTrue(self.user.profile.require_auth)
