# coding: utf-8
import os.path
from io import StringIO, BytesIO
from urllib.parse import urljoin

import requests
from django.contrib.auth import authenticate
from django.core.files.storage import get_storage_class
from django.core.files.uploadedfile import UploadedFile
from django.urls import reverse
from django.test import RequestFactory
from django_digest.test import Client as DigestClient
from httmock import urlmatch, HTTMock

from onadata.apps.api.viewsets.xform_list_api import XFormListApi
from onadata.apps.logger.models import Instance, XForm
from onadata.apps.logger.views import download_xform
from onadata.apps.main.models import MetaData
from onadata.apps.main.tests.test_base import TestBase
from onadata.apps.main.views import profile, download_media_data
from onadata.libs.utils.briefcase_client import BriefcaseClient
from onadata.libs.utils.storage import delete_user_storage

storage = get_storage_class()()


def formList(*args, **kwargs):  # noqa
    view = XFormListApi.as_view({'get': 'list'})
    response = view(*args, **kwargs)
    response.render()
    return response


def xformsManifest(*args, **kwargs):  # noqa
    view = XFormListApi.as_view({'get': 'manifest'})
    response = view(*args, **kwargs)
    response.render()
    return response


@urlmatch(netloc=r'(.*\.)?testserver$')
def form_list_xml(url, request, **kwargs):
    response = requests.Response()
    factory = RequestFactory()
    req = factory.get(url.path)
    req.user = authenticate(username='bob', password='bob')
    req.user.profile.require_auth = False
    req.user.profile.save()
    id_string = 'transportation_2011_07_25'
    # Retrieve XForm pk for user bob.
    # SQLite resets PK to 1 every time the table is truncated (i.e. after
    # each test is over) whereas PostgreSQL keeps the last sequence value
    # which makes `xform_id` differ all the time.
    xform_id = (
        XForm.objects.values_list('id', flat=True)
        .filter(user__username='bob')
        .last()
    )
    if url.path.endswith('formList'):
        res = formList(req, username='bob')
    elif url.path.endswith('form.xml'):
        res = download_xform(req, username='bob', id_string=id_string)
    elif url.path.find('xformsManifest') > -1:
        res = xformsManifest(req, username='bob', pk=xform_id)
    elif url.path.find('formid-media') > -1:
        data_id = url.path[url.path.rfind('/') + 1:]
        res = download_media_data(
            req, username='bob', id_string=id_string, data_id=data_id)
        response._content = get_streaming_content(res)
    else:
        res = formList(req, username='bob')
    response.status_code = 200
    if not response._content:
        response._content = res.content
    return response


def get_streaming_content(res):
    tmp = BytesIO()
    for chunk in res.streaming_content:
        tmp.write(chunk)
    content = tmp.getvalue()
    tmp.close()
    return content


@urlmatch(netloc=r'(.*\.)?testserver$')
def instances_xml(url, request, **kwargs):
    response = requests.Response()
    client = DigestClient()
    client.set_authorization('bob', 'bob', 'Digest')
    res = client.get('%s?%s' % (url.path, url.query))
    if res.status_code == 302:
        res = client.get(res['Location'])
        response.encoding = res.get('content-type')
        response._content = get_streaming_content(res)
    else:
        response._content = res.content
    response.status_code = 200
    return response


class TestBriefcaseClient(TestBase):

    def setUp(self):
        TestBase.setUp(self)
        self._publish_transportation_form()
        self._submit_transport_instance_w_attachment()
        src = os.path.join(self.this_directory, "fixtures",
                           "transportation", "screenshot.png")
        uf = UploadedFile(file=open(src, 'rb'), content_type='image/png')
        count = MetaData.objects.count()
        MetaData.media_upload(self.xform, uf)
        self.assertEqual(MetaData.objects.count(), count + 1)
        url = urljoin(
            self.base_url,
            reverse(profile, kwargs={'username': self.user.username})
        )
        self._logout()
        self._create_user_and_login('deno', 'deno')
        self.bc = BriefcaseClient(
            username='bob', password='bob',
            url=url,
            user=self.user
        )

    def test_download_xform_xml(self):
        """
        Download xform via briefcase api
        """
        with HTTMock(form_list_xml):
            self.bc.download_xforms()

        is_local = storage.__class__.__name__ == 'FileSystemStorage'

        forms_folder_path = os.path.join('deno',
                                         'briefcase',
                                         'forms',
                                         self.xform.id_string)
        forms_path = os.path.join(forms_folder_path,
                                  '%s.xml' % self.xform.id_string)
        form_media_path = os.path.join(forms_folder_path, 'form-media')
        media_path = os.path.join(form_media_path, 'screenshot.png')

        if is_local:
            does_root_folder_exist = storage.exists(forms_folder_path)
            does_media_folder_exist = storage.exists(form_media_path)
        else:
            # `django-storage.exists()` does not work with folders on AWS
            sub_folders, files = storage.listdir(forms_folder_path)
            does_root_folder_exist = bool(sub_folders or files)
            does_media_folder_exist = 'form-media' in sub_folders

        self.assertTrue(does_root_folder_exist)
        self.assertTrue(storage.exists(forms_path))
        self.assertTrue(does_media_folder_exist)
        self.assertTrue(storage.exists(media_path))

        """
        Download instance xml
        """
        with HTTMock(instances_xml):
            self.bc.download_instances(self.xform.id_string)

        instance_folder_path = os.path.join(forms_folder_path, 'instances')
        if is_local:
            does_instances_folder_exist = storage.exists(instance_folder_path)
        else:
            sub_folders, _ = storage.listdir(forms_folder_path)
            does_instances_folder_exist = 'instances' in sub_folders

        self.assertTrue(does_instances_folder_exist)

        instance = Instance.objects.all()[0]
        instance_path = os.path.join(
            instance_folder_path, 'uuid%s' % instance.uuid, 'submission.xml')
        self.assertTrue(storage.exists(instance_path))
        media_file = "1335783522563.jpg"
        media_path = os.path.join(
            instance_folder_path, 'uuid%s' % instance.uuid, media_file)
        self.assertTrue(storage.exists(media_path))

    def test_push(self):
        with HTTMock(form_list_xml):
            self.bc.download_xforms()
        with HTTMock(instances_xml):
            self.bc.download_instances(self.xform.id_string)
        XForm.objects.all().delete()
        xforms = XForm.objects.filter(
            user=self.user, id_string=self.xform.id_string)
        self.assertTrue(xforms.count() == 0)
        instances = Instance.objects.filter(
            xform__user=self.user, xform__id_string=self.xform.id_string)
        self.assertTrue(instances.count() == 0)
        self.bc.push()
        xforms = XForm.objects.filter(
            user=self.user, id_string=self.xform.id_string)
        self.assertTrue(xforms.count() == 1)
        instances = Instance.objects.filter(
            xform__user=self.user, xform__id_string=self.xform.id_string)
        self.assertTrue(instances.count() == 1)

    def tearDown(self):
        # remove media files
        for username in ['bob', 'deno']:
            delete_user_storage(username)
