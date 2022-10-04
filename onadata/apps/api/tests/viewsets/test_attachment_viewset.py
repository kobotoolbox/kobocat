# coding: utf-8
import os

import pytest
from django.conf import settings
from kobo_service_account.utils import get_request_headers
from rest_framework import status

from onadata.apps.api.tests.viewsets.test_abstract_viewset import \
    TestAbstractViewSet
from onadata.apps.api.viewsets.attachment_viewset import AttachmentViewSet
from onadata.apps.main.models import UserProfile


class TestAttachmentViewSet(TestAbstractViewSet):

    def setUp(self):
        super().setUp()
        self.retrieve_view = AttachmentViewSet.as_view({
            'get': 'retrieve'
        })
        self.list_view = AttachmentViewSet.as_view({
            'get': 'list'
        })

        self.publish_xls_form()

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

        alice_profile = self._create_user_profile(alice_profile_data)
        self.alice = alice_profile.user

    def _retrieve_view(self, auth_headers):
        self._submit_transport_instance_w_attachment()

        pk = self.attachment.pk
        data = {
            'url': 'http://testserver/api/v1/media/%s' % pk,
            'field_xpath': None,
            'download_url': self.attachment.secure_url(),
            'small_download_url': self.attachment.secure_url('small'),
            'medium_download_url': self.attachment.secure_url('medium'),
            'large_download_url': self.attachment.secure_url('large'),
            'id': pk,
            'xform': self.xform.pk,
            'instance': self.attachment.instance.pk,
            'mimetype': self.attachment.mimetype,
            'filename': self.attachment.media_file.name
        }
        request = self.factory.get('/', **auth_headers)
        response = self.retrieve_view(request, pk=pk)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(isinstance(response.data, dict))

        self.assertEqual(response.data, data)

        # file download
        filename = data['filename']
        ext = filename[filename.rindex('.') + 1:]
        request = self.factory.get('/', **auth_headers)
        response = self.retrieve_view(request, pk=pk, format=ext)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'image/jpeg')

    def test_retrieve_view(self):
        self._retrieve_view(self.extra)

    def test_retrieve_view_with_service_account(self):
        extra = {'HTTP_AUTHORIZATION': f'Token {self.alice.auth_token}'}
        # Alice cannot view bob's attachment and should receive a 404.
        # The first assertion is `response.status_code == 200`, thus it should
        # raise an error
        assertion_pattern = (
            f'{status.HTTP_404_NOT_FOUND} != {status.HTTP_200_OK}'
        )
        with pytest.raises(AssertionError, match=assertion_pattern) as e:
            self._retrieve_view(extra)

        # Try the same request with service account user on behalf of alice
        extra = self.get_meta_from_headers(get_request_headers(self.alice.username))
        # Test server does not provide `host` header
        extra['HTTP_HOST'] = settings.TEST_HTTP_HOST
        self._retrieve_view(extra)

    def test_list_view(self):
        self._submit_transport_instance_w_attachment()

        request = self.factory.get('/', **self.extra)
        response = self.list_view(request)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(isinstance(response.data, list))

    def test_list_view_filter_by_xform(self):
        self._submit_transport_instance_w_attachment()

        data = {
            'xform': self.xform.pk
        }
        request = self.factory.get('/', data, **self.extra)
        response = self.list_view(request)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(isinstance(response.data, list))

        data['xform'] = 10000000
        request = self.factory.get('/', data, **self.extra)
        response = self.list_view(request)
        self.assertEqual(response.status_code, 404)

        data['xform'] = 'lol'
        request = self.factory.get('/', data, **self.extra)
        response = self.list_view(request)
        self.assertEqual(response.status_code, 400)

    def test_list_view_filter_by_instance(self):
        self._submit_transport_instance_w_attachment()

        data = {
            'instance': self.attachment.instance.pk
        }
        request = self.factory.get('/', data, **self.extra)
        response = self.list_view(request)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(isinstance(response.data, list))

        data['instance'] = 10000000
        request = self.factory.get('/', data, **self.extra)
        response = self.list_view(request)
        self.assertEqual(response.status_code, 404)

        data['instance'] = 'lol'
        request = self.factory.get('/', data, **self.extra)
        response = self.list_view(request)
        self.assertEqual(response.status_code, 400)

    def test_direct_image_link(self):
        self._submit_transport_instance_w_attachment()

        data = {
            'filename': self.attachment.media_file.name
        }
        request = self.factory.get('/', data, **self.extra)
        response = self.retrieve_view(request, pk=self.attachment.pk)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(isinstance(response.data, str))
        self.assertEqual(response.data, self.attachment.secure_url())

        data['filename'] = 10000000
        request = self.factory.get('/', data, **self.extra)
        response = self.retrieve_view(request, pk=self.attachment.instance.pk)
        self.assertEqual(response.status_code, 404)

        data['filename'] = 'lol'
        request = self.factory.get('/', data, **self.extra)
        response = self.retrieve_view(request, pk=self.attachment.instance.pk)
        self.assertEqual(response.status_code, 404)

    def test_direct_image_link_uppercase(self):
        self._submit_transport_instance_w_attachment(
            media_file="1335783522564.JPG")

        filename = self.attachment.media_file.name
        file_base, file_extension = os.path.splitext(filename)
        data = {
            'filename': file_base + file_extension.upper()
        }
        request = self.factory.get('/', data, **self.extra)
        response = self.retrieve_view(request, pk=self.attachment.pk)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(isinstance(response.data, str))
        self.assertEqual(response.data, self.attachment.secure_url())

    def test_attachment_storage_bytes_create_instance_defer_counting(self):
        """
        The normal submission mechanism invokes "defer_counting" to trigger the
        counters calculation at the end of the transaction only, to avoid a
        bottleneck when data is saved.
        """
        self._submit_transport_instance_w_attachment()
        media_file_size = self.attachment.media_file_size

        self.xform.refresh_from_db()
        self.assertEqual(self.xform.attachment_storage_bytes, media_file_size)

        profile = UserProfile.objects.get(user=self.xform.user)
        self.assertEqual(profile.attachment_storage_bytes, media_file_size)

    def test_attachment_storage_bytes_delete_signal(self):
        self.test_attachment_storage_bytes_create_instance_defer_counting()
        self.attachment.delete()
        self.xform.refresh_from_db()
        self.assertEqual(self.xform.attachment_storage_bytes, 0)
        profile = UserProfile.objects.get(user=self.xform.user)
        self.assertEqual(profile.attachment_storage_bytes, 0)

    def test_attachment_storage_bytes_create_instance_signal(self):
        """
        Creating a new submission first and then adding an attachment by
        submitting the same XML alongside that attachment uses the signal
        logic instead of the `defer_counting` performance-optimization logic.

        This method copies some code from
        `_submit_transport_instance_w_attachment()`
        """
        survey_datetime = self.surveys[0]
        xml_path = os.path.join(
            self.main_directory,
            'fixtures',
            'transportation',
            'instances',
            survey_datetime,
            f'{survey_datetime}.xml',
        )
        media_file_path = os.path.join(
            self.main_directory,
            'fixtures',
            'transportation',
            'instances',
            survey_datetime,
            '1335783522563.jpg'
        )
        xform = self.xform
        user_profile = UserProfile.objects.get(user=xform.user)
        # First, submit the XML with no attachments
        self._make_submission(xml_path)
        self.assertEqual(self.xform.instances.count(), 1)
        submission_uuid = self.xform.instances.first().uuid
        self.xform.refresh_from_db()
        self.assertEqual(xform.attachment_storage_bytes, 0)
        user_profile.refresh_from_db()
        self.assertEqual(user_profile.attachment_storage_bytes, 0)
        # Submit the same XML again, but this time include the attachment
        with open(media_file_path, 'rb') as media_file:
            self._make_submission(xml_path, media_file=media_file)
        self.assertEqual(self.xform.instances.count(), 1)
        self.assertEqual(self.xform.instances.first().uuid, submission_uuid)
        media_file_size = os.path.getsize(media_file_path)
        self.xform.refresh_from_db()
        self.assertEqual(xform.attachment_storage_bytes, media_file_size)
        user_profile.refresh_from_db()
        self.assertEqual(user_profile.attachment_storage_bytes, media_file_size)
