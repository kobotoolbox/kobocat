# coding: utf-8
from __future__ import unicode_literals, print_function, division, absolute_import

import re
import requests

from time import time
from httmock import HTTMock, all_requests

from django.test import RequestFactory
from django.core.urlresolvers import reverse
from django.core.validators import URLValidator
from django.conf import settings
from nose import SkipTest

from onadata.apps.main.views import set_perm, show, qrcode
from onadata.apps.logger.views import enter_data
from onadata.libs.utils.viewer_tools import enketo_url
from .test_base import TestBase


@all_requests
def enketo_mock(url, request):
    response = requests.Response()
    response.status_code = 201
    response._content = '{"url": "https://hmh2a.enketo.formhub.org"}'
    return response


@all_requests
def enketo_error_mock(url, request):
    response = requests.Response()
    response.status_code = 400
    response._content = '{"message": ' \
                        '"no account exists for this OpenRosa server"}'
    return response


class TestFormEnterData(TestBase):
    """
    This class is deprecated and is going to be removed in KoBoCAT 2.0
    Notes: skipped tests have been removed
    """

    def setUp(self):
        TestBase.setUp(self)
        self._create_user_and_login()
        self._publish_transportation_form_and_submit_instance()
        self.perm_url = reverse(set_perm, kwargs={
            'username': self.user.username, 'id_string': self.xform.id_string})
        self.show_url = reverse(show, kwargs={'uuid': self.xform.uuid})
        self.url = reverse(enter_data, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string
        })

    def _running_enketo(self, check_url=False):
        if hasattr(settings, 'ENKETO_URL') and \
                (not check_url or self._check_url(settings.ENKETO_URL)):
            return True
        return False

    def test_enketo_remote_server(self):
        if not self._running_enketo():
            raise SkipTest
        with HTTMock(enketo_mock):
            server_url = 'https://testserver.com/bob'
            form_id = "test_%s" % re.sub(re.compile("\."), "_", str(time()))
            url = enketo_url(server_url, form_id)
            self.assertIsInstance(url, basestring)
            self.assertIsNone(URLValidator()(url))

    def _get_grcode_view_response(self):
        factory = RequestFactory()
        request = factory.get('/')
        request.user = self.user
        response = qrcode(
            request, self.user.username, self.xform.id_string)

        return response

    def test_enter_data_no_permission(self):
        response = self.anon.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_enter_data_non_existent_user(self):
        url = reverse(enter_data, kwargs={
            'username': 'nonexistentuser',
            'id_string': self.xform.id_string
        })
        response = self.anon.get(url)
        self.assertEqual(response.status_code, 404)
