# coding: utf-8
import os

from django.urls import reverse
from guardian.shortcuts import assign_perm, remove_perm

from onadata.apps.main.views import show
from .test_base import TestBase


class TestPermissions(TestBase):

    def setUp(self):
        TestBase.setUp(self)
        self._create_user_and_login()
        self._publish_transportation_form()
        s = 'transport_2011-07-25_19-05-49'
        self._make_submission(os.path.join(
            self.this_directory, 'fixtures',
            'transportation', 'instances', s, s + '.xml'))
        self.submission = self.xform.instances.reverse()[0]
        self.url = reverse(show, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string
        })

    def test_set_permissions_for_user(self):
        # alice cannot view bob's forms
        # `self.xform` belongs to bob
        self._create_user_and_login('alice', 'alice')
        # Alice is `self.user` now.
        self.assertEqual(self.user.has_perm('view_xform', self.xform), False)
        self.assertEqual(self.user.has_perm('change_xform', self.xform), False)
        assign_perm('view_xform', self.user, self.xform)
        self.assertEqual(self.user.has_perm('view_xform', self.xform), True)
        assign_perm('change_xform', self.user, self.xform)
        self.assertEqual(self.user.has_perm('change_xform', self.xform), True)
        xform = self.xform

        remove_perm('view_xform', self.user, xform)
        self.assertEqual(self.user.has_perm('view_xform', xform), False)
        remove_perm('change_xform', self.user, xform)
        self.assertEqual(self.user.has_perm('change_xform', xform), False)

        self._publish_transportation_form()
        self.assertNotEqual(xform, self.xform)
        # Alice is the owner of `self.xform`
        self.assertEqual(self.user.has_perm('view_xform', self.xform), True)
        self.assertEqual(self.user.has_perm('change_xform', self.xform), True)

    def test_add_view_to_user(self):
        self._create_user_and_login('alice', 'alice')
        alice = self.user
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        assign_perm('view_xform', alice, self.xform)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
