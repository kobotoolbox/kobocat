# coding: utf-8
import os
from unittest import skip

from django.core.files.base import ContentFile
from django.urls import reverse

from onadata import koboform
from onadata.apps.main.views import show, form_photos, \
    show_form_settings
from onadata.apps.logger.models import XForm
from onadata.apps.logger.views import download_xlsform, download_jsonform, \
    download_xform
from onadata.apps.viewer.views import export_list
from onadata.libs.utils.logger_tools import publish_xml_form
from onadata.libs.utils.user_auth import http_auth_string
from .test_base import TestBase


class TestFormShow(TestBase):

    def setUp(self):
        TestBase.setUp(self)
        self._create_user_and_login()
        self._publish_transportation_form()
        self.url = reverse(show, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string
        })

    def test_show_form_name(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.xform.id_string)

    def test_hide_from_anon(self):
        response = self.anon.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_hide_from_not_user(self):
        self._create_user_and_login("jo")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_show_to_anon_if_public(self):
        self.xform.shared = True
        self.xform.save()
        response = self.anon.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_dl_xlsx_xlsform(self):
        self._publish_xlsx_file()
        response = self.client.get(reverse(download_xlsform, kwargs={
            'username': self.user.username,
            'id_string': 'exp_one'
        }))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response['Content-Disposition'],
            "attachment; filename=exp_one.xlsx")

    def test_dl_xls_redirect_to_login_to_anon_if_public(self):
        self.xform.shared = True
        self.xform.save()
        response = self.anon.get(reverse(download_xlsform, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string
        }))

        login_url = reverse('auth_login')
        if koboform.active and koboform.autoredirect:
            redirect_to = koboform.login_url()
        else:
            redirect_to = login_url
        self.assertEqual(response.url, redirect_to)
        self.assertEqual(response.status_code, 302)

    def test_dl_xls_for_basic_auth(self):
        extra = {
            'HTTP_AUTHORIZATION':
            http_auth_string(self.login_username, self.login_password)
        }
        response = self.anon.get(reverse(download_xlsform, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string
        }), **extra)
        self.assertEqual(response.status_code, 200)

    def test_dl_json_to_anon_if_public(self):
        self.xform.shared = True
        self.xform.save()
        response = self.anon.get(reverse(download_jsonform, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string
        }))
        self.assertEqual(response.status_code, 200)

    def test_dl_jsonp_to_anon_if_public(self):
        self.xform.shared = True
        self.xform.save()
        callback = 'jsonpCallback'
        response = self.anon.get(reverse(download_jsonform, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string
        }), {'callback': callback})
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertEqual(content.startswith(callback + '('), True)
        self.assertEqual(content.endswith(')'), True)

    def test_dl_json_for_basic_auth(self):
        extra = {
            'HTTP_AUTHORIZATION':
            http_auth_string(self.login_username, self.login_password)
        }
        response = self.anon.get(reverse(download_jsonform, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string
        }), **extra)
        self.assertEqual(response.status_code, 200)

    def test_dl_json_for_cors_options(self):
        response = self.anon.options(reverse(download_jsonform, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string
        }))
        allowed_headers = ['Accept', 'Origin', 'X-Requested-With',
                           'Authorization']
        control_headers = response['Access-Control-Allow-Headers']
        provided_headers = [h.strip() for h in control_headers.split(',')]
        self.assertListEqual(allowed_headers, provided_headers)
        self.assertEqual(response['Access-Control-Allow-Methods'], 'GET')
        self.assertEqual(response['Access-Control-Allow-Origin'], '*')

    def test_dl_xform_to_anon_if_public(self):
        self.xform.shared = True
        self.xform.save()
        response = self.anon.get(reverse(download_xform, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string
        }))
        self.assertEqual(response.status_code, 200)

    def test_dl_xform_for_basic_auth(self):
        extra = {
            'HTTP_AUTHORIZATION':
            http_auth_string(self.login_username, self.login_password)
        }
        response = self.anon.get(reverse(download_xform, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string
        }), **extra)
        self.assertEqual(response.status_code, 200)

    def test_dl_xform_for_authenticated_non_owner(self):
        self._create_user_and_login('alice', 'alice')
        response = self.client.get(reverse(download_xform, kwargs={
            'username': 'bob',
            'id_string': self.xform.id_string
        }))
        self.assertEqual(response.status_code, 200)

    def test_show_link_if_shared_and_data(self):
        self.xform.shared = True
        self.xform.shared_data = True
        self.xform.save()
        self._submit_transport_instance()
        response = self.anon.get(self.url)
        self.assertContains(response, reverse(export_list, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string,
            'export_type': 'csv'
        }))

    def test_show_link_if_owner(self):
        self._submit_transport_instance()
        response = self.client.get(self.url)
        self.assertContains(response, reverse(export_list, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string,
            'export_type': 'csv'
        }))
        self.assertContains(response, reverse(export_list, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string,
            'export_type': 'xls'
        }))
        self.assertNotContains(response, 'GPS Points')

        # check that a form with geopoints has the map url
        response = self._publish_xls_file(
            os.path.join(
                os.path.dirname(__file__), "fixtures", "gps", "gps.xls"))
        self.assertEqual(response.status_code, 201)
        self.xform = XForm.objects.latest('date_created')

        show_url = reverse(show, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string
        })

        response = self.client.get(show_url)
        # check that map url doesnt show before we have submissions
        self.assertNotContains(response, 'GPS Points')

        # make a submission
        self._make_submission(
            os.path.join(
                os.path.dirname(__file__), "fixtures", "gps", "instances",
                "gps_1980-01-23_20-52-08.xml")
        )
        self.assertEqual(self.response.status_code, 201)
        # get new show view
        response = self.client.get(show_url)
        self.assertContains(response, 'GPS Points')

    def test_anon_no_toggle_data_share_btn(self):
        self.xform.shared = True
        self.xform.save()
        response = self.anon.get(self.url)
        self.assertNotContains(response, 'PUBLIC</a>')
        self.assertNotContains(response, 'PRIVATE</a>')

    def test_show_add_supporting_media_if_owner(self):
        url = reverse(show_form_settings, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string
        })
        response = self.client.get(url)
        self.assertContains(response, 'Media Upload')

    def test_load_photo_page(self):
        response = self.client.get(reverse(form_photos, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string}))
        self.assertEqual(response.status_code, 200)

    def test_load_from_uuid(self):
        self.xform = XForm.objects.get(pk=self.xform.id)
        response = self.client.get(reverse(show, kwargs={
            'uuid': self.xform.uuid}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], self.url)

    def test_publish_xml_xlsform_download(self):
        count = XForm.objects.count()
        path = os.path.join(
            self.this_directory, '..', '..', 'api', 'tests', 'fixtures',
            'forms', 'contributions', 'contributions.xml')
        f = open(path, 'rb')
        xml_file = ContentFile(f.read())
        f.close()
        xml_file.name = 'contributions.xml'
        self.xform = publish_xml_form(xml_file, self.user)
        self.assertTrue(XForm.objects.count() > count)
        response = self.client.get(reverse(download_xlsform, kwargs={
            'username': self.user.username,
            'id_string': 'contributions'
        }), follow=True)
        self.assertContains(response, 'No XLS file for your form ')
