# coding: utf-8
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory
from django_digest.test import DigestAuth

from onadata.apps.api.viewsets.xform_list_api import XFormListApi
from onadata.apps.main.tests.test_base import TestBase


def formList(*args, **kwargs):  # noqa
    view = XFormListApi.as_view({'get': 'list'})
    return view(*args, **kwargs)


class TestFormList(TestBase):
    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()

    def test_returns_200_for_owner(self):
        self._set_require_auth()
        request = self.factory.get('/')
        auth = DigestAuth('bob', 'bob')
        response = formList(request, username=self.user.username)
        request.META.update(auth(request.META, response))
        response = formList(request, username=self.user.username)
        self.assertEqual(response.status_code, 200)

    def test_return_401_for_anon_when_require_auth_true(self):
        self._set_require_auth()
        request = self.factory.get('/')
        response = formList(request, username=self.user.username)
        self.assertEqual(response.status_code, 401)

    def test_returns_200_for_authenticated_non_owner(self):
        self._set_require_auth()
        credentials = ('alice', 'alice',)
        self._create_user(*credentials)
        auth = DigestAuth('alice', 'alice')
        request = self.factory.get('/')
        response = formList(request, username=self.user.username)
        request.META.update(auth(request.META, response))
        response = formList(request, username=self.user.username)
        self.assertEqual(response.status_code, 200)

    def test_show_for_anon_when_require_auth_false(self):
        request = self.factory.get('/')
        request.user = AnonymousUser()
        response = formList(request, username=self.user.username)
        self.assertEqual(response.status_code, 200)
