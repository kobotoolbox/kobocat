# coding: utf-8
import os

from django.urls import reverse
from django.contrib.auth import authenticate
from rest_framework.test import APIRequestFactory

from onadata.apps.api.viewsets.xform_submission_api import XFormSubmissionApi
from onadata.apps.main.tests.test_base import TestBase
from onadata.apps.logger.models import Attachment
from onadata.apps.logger.models import Instance
from onadata.apps.logger.models import XForm


class TestEncryptedForms(TestBase):

    def setUp(self):
        super(TestBase, self).setUp()
        self._create_user_and_login()
        self._submission_url = reverse(
            'submissions', kwargs={'username': self.user.username})

    def test_encrypted_submissions(self):
        self._publish_xls_file(os.path.join(
            self.this_directory, 'fixtures', 'transportation',
            'transportation_encrypted.xls'
        ))
        xform = XForm.objects.get(id_string='transportation_encrypted')
        self.assertTrue(xform.encrypted)
        uuid = "c15252fe-b6f3-4853-8f04-bf89dc73985a"
        with self.assertRaises(Instance.DoesNotExist):
            Instance.objects.get(uuid=uuid)
        message = "Successful submission."
        files = {}
        for filename in ['submission.xml', 'submission.xml.enc']:
            files[filename] = os.path.join(
                self.this_directory, 'fixtures', 'transportation',
                'instances_encrypted', filename)
        count = Instance.objects.count()
        attachments_count = Attachment.objects.count()

        with open(files['submission.xml.enc'], 'rb') as ef:
            with open(files['submission.xml'], 'rb') as f:
                post_data = {
                    'xml_submission_file': f,
                    'submission.xml.enc': ef}
                self.factory = APIRequestFactory()
                request = self.factory.post(self._submission_url, post_data)
                request.user = authenticate(username='bob',
                                            password='bob')
                response = self.submission_view(request, username=self.user.username)
                self.assertContains(response, message, status_code=201)
                self.assertEqual(Instance.objects.count(), count + 1)
                self.assertEqual(Attachment.objects.count(), attachments_count + 1)
                self.assertTrue(Instance.objects.get(uuid=uuid))
