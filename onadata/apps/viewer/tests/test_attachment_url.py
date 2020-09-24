# coding: utf-8
from __future__ import unicode_literals, print_function, division, absolute_import

from django.core.urlresolvers import reverse

from onadata.apps.main.tests.test_base import TestBase
from onadata.apps.logger.models import Attachment
from onadata.apps.viewer.views import attachment_url
from onadata.libs.utils.storage import delete_user_storage


class TestAttachmentUrl(TestBase):

    def setUp(self):
        self.attachment_count = 0
        TestBase.setUp(self)
        self._create_user_and_login()
        self._publish_transportation_form()
        self._submit_transport_instance_w_attachment()
        self.url = reverse(
            attachment_url, kwargs={'size': 'original'})

    def test_attachment_url(self):
        self.assertEqual(
            Attachment.objects.count(), self.attachment_count + 1)
        response = self.client.get(
            self.url, {"media_file": self.attachment_media_file})
        self.assertEqual(response.status_code, 200)  # nginx is used as proxy

    def test_attachment_not_found(self):
        response = self.client.get(
            self.url, {"media_file": "non_existent_attachment.jpg"})
        self.assertEqual(response.status_code, 404)

    def test_attachment_has_mimetype(self):
        attachment = Attachment.objects.all().reverse()[0]
        self.assertEqual(attachment.mimetype, 'image/jpeg')

    def tearDown(self):
        if self.user:
            delete_user_storage(self.user.username)
