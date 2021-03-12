# coding: utf-8
import os
import hashlib

from django.core.files.base import File
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.urlresolvers import reverse

from onadata.apps.main.models import MetaData
from onadata.apps.main.views import (
    show,
    edit,
    download_media_data,
)
from .test_base import TestBase


class TestFormMetadata(TestBase):

    def setUp(self):
        TestBase.setUp(self)
        self._create_user_and_login()
        self._publish_transportation_form_and_submit_instance()
        self.url = reverse(show, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string
        })
        self.edit_url = reverse(edit, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string
        })

    def _add_metadata(self):
        name = 'screenshot.png'
        data_type = 'media'
        path = os.path.join(self.this_directory, "fixtures",
                            "transportation", name)
        with open(path, 'rb') as doc_file:
            self.post_data = {
                data_type: doc_file
            }
            self.client.post(self.edit_url, self.post_data)

        self.doc = MetaData.objects.filter(data_type=data_type).reverse()[0]
        self.doc_url = reverse(download_media_data, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string,
            'data_id': self.doc.id})

        return name

    def test_adds_supporting_media_on_submit(self):
        count = len(MetaData.objects.filter(xform=self.xform,
                    data_type='media'))
        self._add_metadata()
        self.assertEquals(count + 1, len(MetaData.objects.filter(
            xform=self.xform, data_type='media')))

    def test_download_supporting_media(self):
        self._add_metadata()
        response = self.client.get(self.doc_url)
        self.assertEqual(response.status_code, 200)
        fileName, ext = os.path.splitext(response['Content-Disposition'])
        self.assertEqual(ext, '.png')

    def test_shared_download_supporting_media_for_anon(self):
        self._add_metadata()
        self.xform.shared = True
        self.xform.save()
        response = self.anon.get(self.doc_url)
        self.assertEqual(response.status_code, 200)

    def test_delete_supporting_media(self):
        count = MetaData.objects.filter(
            xform=self.xform, data_type='media').count()
        self._add_metadata()
        self.assertEqual(MetaData.objects.filter(
            xform=self.xform, data_type='media').count(), count + 1)
        response = self.client.get(self.doc_url + '?del=true')
        self.assertEqual(MetaData.objects.filter(
            xform=self.xform, data_type='media').count(), count)
        self.assertEqual(response.status_code, 302)
        self._add_metadata()
        response = self.anon.get(self.doc_url + '?del=true')
        self.assertEqual(MetaData.objects.filter(
            xform=self.xform, data_type='media').count(), count + 1)
        self.assertEqual(response.status_code, 403)

    def test_media_file_hash(self):
        name = "screenshot.png"
        media_file = os.path.join(
            self.this_directory, 'fixtures', 'transportation', name)
        m = MetaData.objects.create(
            data_type='media', xform=self.xform, data_value=name,
            data_file=File(open(media_file, 'rb'), name),
            data_file_type='image/png')
        f = open(media_file, 'rb')
        md5_hash = hashlib.md5(f.read()).hexdigest()
        media_hash = f'md5:{md5_hash}'
        f.close()
        meta_hash = m.hash
        self.assertEqual(meta_hash, media_hash)
        self.assertEqual(m.file_hash, media_hash)

    def test_add_media_url(self):
        uri = 'https://devtrac.ona.io/fieldtrips.csv'
        count = MetaData.objects.filter(data_type='media').count()
        self.client.post(self.edit_url, {'media_url': uri})
        self.assertEqual(count + 1,
                          len(MetaData.objects.filter(data_type='media')))

    def test_windows_csv_file_upload(self):
        count = MetaData.objects.filter(data_type='media').count()
        media_file = os.path.join(
            self.this_directory, 'fixtures', 'transportation',
            'transportation.csv')
        f = InMemoryUploadedFile(open(media_file),
                                 'media',
                                 'transportation.csv',
                                 'application/octet-stream',
                                 2625,
                                 None)
        MetaData.media_upload(self.xform, f)
        media_list = MetaData.objects.filter(data_type='media')
        new_count = media_list.count()
        self.assertEqual(count + 1, new_count)
        media = media_list.get(data_value='transportation.csv')
        self.assertEqual(media.data_file_type, 'text/csv')
