# coding: utf-8
import os

from django.conf import settings
from django_digest.test import DigestAuth
from guardian.shortcuts import assign_perm

from onadata.apps.api.tests.viewsets.test_abstract_viewset import\
    TestAbstractViewSet
from onadata.apps.api.viewsets.xform_list_api import XFormListApi
from onadata.libs.constants import (
    CAN_ADD_SUBMISSIONS,
    CAN_VIEW_XFORM
)


class TestXFormListApi(TestAbstractViewSet):
    def setUp(self):
        super().setUp()
        self.view = XFormListApi.as_view({
            "get": "list"
        })
        self.publish_xls_form()

    def test_get_xform_list(self):
        request = self.factory.get('/')
        response = self.view(request)
        self.assertEqual(response.status_code, 401)
        auth = DigestAuth('bob', 'bobbob')
        request.META.update(auth(request.META, response))
        response = self.view(request)
        self.assertEqual(response.status_code, 200)

        path = os.path.join(
            os.path.dirname(__file__),
            '..', 'fixtures', 'formList.xml')

        with open(path, 'r') as f:
            form_list_xml = f.read().strip()
            data = {"hash": self.xform.md5_hash, "pk": self.xform.pk}
            content = response.render().content
            self.assertEqual(content.decode('utf-8'), form_list_xml % data)
            self.assertTrue(response.has_header('X-OpenRosa-Version'))
            self.assertTrue(
                response.has_header('X-OpenRosa-Accept-Content-Length'))
            self.assertTrue(response.has_header('Date'))
            self.assertEqual(response['Content-Type'],
                             'text/xml; charset=utf-8')

    def test_get_xform_list_inactive_form(self):
        self.xform.downloadable = False
        self.xform.save()
        request = self.factory.get('/')
        response = self.view(request)
        self.assertEqual(response.status_code, 401)
        auth = DigestAuth('bob', 'bobbob')
        request.META.update(auth(request.META, response))
        response = self.view(request)
        self.assertEqual(response.status_code, 200)

        xml = '<?xml version="1.0" encoding="utf-8"?>\n<xforms '
        xml += 'xmlns="http://openrosa.org/xforms/xformsList"></xforms>'
        content = response.render().content.decode('utf-8')
        self.assertEqual(content, xml)
        self.assertTrue(response.has_header('X-OpenRosa-Version'))
        self.assertTrue(
            response.has_header('X-OpenRosa-Accept-Content-Length'))
        self.assertTrue(response.has_header('Date'))
        self.assertEqual(response['Content-Type'],
                         'text/xml; charset=utf-8')

    def test_get_xform_list_anonymous_user(self):
        request = self.factory.get('/')
        response = self.view(request)
        self.assertEqual(response.status_code, 401)
        response = self.view(request, username=self.user.username)
        self.assertEqual(response.status_code, 200)

        path = os.path.join(
            os.path.dirname(__file__),
            '..', 'fixtures', 'formList.xml')

        with open(path, 'r') as f:
            form_list_xml = f.read().strip()
            data = {"hash": self.xform.md5_hash, "pk": self.xform.pk}
            content = response.render().content
            self.assertEqual(content.decode('utf-8'), form_list_xml % data)
            self.assertTrue(response.has_header('X-OpenRosa-Version'))
            self.assertTrue(
                response.has_header('X-OpenRosa-Accept-Content-Length'))
            self.assertTrue(response.has_header('Date'))
            self.assertEqual(response['Content-Type'],
                             'text/xml; charset=utf-8')

    def test_get_xform_list_anonymous_user_require_auth(self):
        self.user.profile.require_auth = True
        self.user.profile.save()
        request = self.factory.get('/')
        response = self.view(request)
        self.assertEqual(response.status_code, 401)
        response = self.view(request, username=self.user.username)
        self.assertEqual(response.status_code, 401)

    def test_get_xform_list_other_user_with_no_role(self):
        request = self.factory.get('/')
        response = self.view(request)
        alice_data = {
            'username': 'alice',
            'password1': 'alicealice',
            'password2': 'alicealice',
            'email': 'alice@localhost.com',
        }
        alice_profile = self._create_user_profile(alice_data)

        self.assertFalse(
            alice_profile.user.has_perms([CAN_VIEW_XFORM], self.xform)
        )

        auth = DigestAuth('alice', 'alicealice')
        request.META.update(auth(request.META, response))
        response = self.view(request)
        self.assertEqual(response.status_code, 200)
        content = response.render().content.decode('utf-8')
        self.assertNotIn(self.xform.id_string, content)
        self.assertEqual(
            content, '<?xml version="1.0" encoding="utf-8"?>\n<xforms '
            'xmlns="http://openrosa.org/xforms/xformsList"></xforms>')
        self.assertTrue(response.has_header('X-OpenRosa-Version'))
        self.assertTrue(
            response.has_header('X-OpenRosa-Accept-Content-Length'))
        self.assertTrue(response.has_header('Date'))
        self.assertEqual(response['Content-Type'], 'text/xml; charset=utf-8')

    def test_get_xform_list_other_user_with_readonly_role(self):
        request = self.factory.get('/')
        response = self.view(request)
        alice_data = {
            'username': 'alice',
            'password1': 'alicealice',
            'password2': 'alicealice',
            'email': 'alice@localhost.com',
        }
        alice_profile = self._create_user_profile(alice_data)

        assign_perm(CAN_VIEW_XFORM, alice_profile.user, self.xform)
        self.assertTrue(
            alice_profile.user.has_perms([CAN_VIEW_XFORM], self.xform)
        )

        auth = DigestAuth('alice', 'alicealice')
        request.META.update(auth(request.META, response))
        response = self.view(request)
        self.assertEqual(response.status_code, 200)
        content = response.render().content.decode('utf-8')
        self.assertNotIn(self.xform.id_string, content)
        self.assertEqual(
            content, '<?xml version="1.0" encoding="utf-8"?>\n<xforms '
            'xmlns="http://openrosa.org/xforms/xformsList"></xforms>')
        self.assertTrue(response.has_header('X-OpenRosa-Version'))
        self.assertTrue(
            response.has_header('X-OpenRosa-Accept-Content-Length'))
        self.assertTrue(response.has_header('Date'))
        self.assertEqual(response['Content-Type'], 'text/xml; charset=utf-8')

    def test_get_xform_list_other_user_with_dataentry_role(self):
        request = self.factory.get('/')
        response = self.view(request)
        alice_data = {
            'username': 'alice',
            'password1': 'alicealice',
            'password2': 'alicealice',
            'email': 'alice@localhost.com',
        }
        alice_profile = self._create_user_profile(alice_data)

        assign_perm(CAN_ADD_SUBMISSIONS, alice_profile.user, self.xform)
        self.assertTrue(
            alice_profile.user.has_perms([CAN_ADD_SUBMISSIONS], self.xform)
        )

        auth = DigestAuth('alice', 'alicealice')
        request.META.update(auth(request.META, response))
        response = self.view(request)
        self.assertEqual(response.status_code, 200)

        path = os.path.join(
            os.path.dirname(__file__),
            '..', 'fixtures', 'formList.xml')

        with open(path, 'r') as f:
            form_list_xml = f.read().strip()
            data = {"hash": self.xform.md5_hash, "pk": self.xform.pk}
            content = response.render().content
            self.assertEqual(content.decode('utf-8'), form_list_xml % data)
            self.assertTrue(response.has_header('X-OpenRosa-Version'))
            self.assertTrue(
                response.has_header('X-OpenRosa-Accept-Content-Length'))
            self.assertTrue(response.has_header('Date'))
            self.assertEqual(response['Content-Type'],
                             'text/xml; charset=utf-8')

    def test_get_xform_list_with_formid_parameter(self):
        """
        Test `formList` with `?formID=[id_string]` filter
        """
        # Test unrecognized `formID`
        request = self.factory.get('/', {'formID': 'unrecognizedID'})
        response = self.view(request, username=self.user.username)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

        # Test a valid `formID`
        request = self.factory.get('/', {'formID': self.xform.id_string})
        response = self.view(request, username=self.user.username)
        self.assertEqual(response.status_code, 200)
        path = os.path.join(
            os.path.dirname(__file__), '..', 'fixtures', 'formList.xml'
        )

        with open(path) as f:
            form_list_xml = f.read().strip()
            data = {"hash": self.xform.md5_hash, "pk": self.xform.pk}
            content = response.render().content.decode('utf-8')
            self.assertEqual(content, form_list_xml % data)

    def test_retrieve_xform_xml(self):
        self.view = XFormListApi.as_view({
            "get": "retrieve"
        })
        request = self.factory.head('/')
        response = self.view(request, pk=self.xform.pk)
        auth = DigestAuth('bob', 'bobbob')
        request = self.factory.get('/')
        request.META.update(auth(request.META, response))
        response = self.view(request, pk=self.xform.pk)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response['Content-Type'],
                         'text/xml; charset=utf-8')
        self.assertTrue(response.has_header('X-OpenRosa-Version'))
        self.assertTrue(
            response.has_header('X-OpenRosa-Accept-Content-Length'))
        self.assertTrue(response.has_header('Date'))

        path = os.path.join(
            os.path.dirname(__file__),
            '..', 'fixtures', 'Transportation Form.xml')

        with open(path) as f:
            form_xml = f.read().strip()
            data = {"form_uuid": self.xform.uuid}
            content = response.render().content.decode('utf-8').strip()
            self.assertEqual(content, form_xml % data)

    def _load_metadata(self, xform=None):
        data_value = "screenshot.png"
        data_type = 'media'
        fixture_dir = os.path.join(
            settings.ONADATA_DIR, "apps", "main", "tests", "fixtures",
            "transportation"
        )
        path = os.path.join(fixture_dir, data_value)
        xform = xform or self.xform

        self._add_form_metadata(xform, data_type, data_value, path)

    def test_retrieve_xform_manifest(self):
        self._load_metadata(self.xform)
        self.view = XFormListApi.as_view({
            "get": "manifest"
        })
        request = self.factory.head('/')
        response = self.view(request, pk=self.xform.pk)
        auth = DigestAuth('bob', 'bobbob')
        request = self.factory.get('/')
        request.META.update(auth(request.META, response))
        response = self.view(request, pk=self.xform.pk)
        self.assertEqual(response.status_code, 200)

        manifest_xml = """<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns="http://openrosa.org/xforms/xformsManifest"><mediaFile><filename>screenshot.png</filename><hash>%(hash)s</hash><downloadUrl>http://testserver/bob/xformsMedia/%(xform)s/%(pk)s.png</downloadUrl></mediaFile></manifest>"""  # noqa
        data = {"hash": self.metadata.md5_hash, "pk": self.metadata.pk,
                "xform": self.xform.pk}
        content = response.render().content.decode('utf-8').strip()
        self.assertEqual(content, manifest_xml % data)
        self.assertTrue(response.has_header('X-OpenRosa-Version'))
        self.assertTrue(
            response.has_header('X-OpenRosa-Accept-Content-Length'))
        self.assertTrue(response.has_header('Date'))
        self.assertEqual(response['Content-Type'], 'text/xml; charset=utf-8')

    def test_retrieve_xform_manifest_anonymous_user(self):
        self._load_metadata(self.xform)
        self.view = XFormListApi.as_view({
            "get": "manifest"
        })
        request = self.factory.get('/')
        response = self.view(request, pk=self.xform.pk)
        self.assertEqual(response.status_code, 401)
        response = self.view(request, pk=self.xform.pk,
                             username=self.user.username)
        self.assertEqual(response.status_code, 200)

        manifest_xml = """<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns="http://openrosa.org/xforms/xformsManifest"><mediaFile><filename>screenshot.png</filename><hash>%(hash)s</hash><downloadUrl>http://testserver/bob/xformsMedia/%(xform)s/%(pk)s.png</downloadUrl></mediaFile></manifest>"""  # noqa
        data = {"hash": self.metadata.md5_hash, "pk": self.metadata.pk,
                "xform": self.xform.pk}
        content = response.render().content.decode('utf-8').strip()
        self.assertEqual(content, manifest_xml % data)
        self.assertTrue(response.has_header('X-OpenRosa-Version'))
        self.assertTrue(
            response.has_header('X-OpenRosa-Accept-Content-Length'))
        self.assertTrue(response.has_header('Date'))
        self.assertEqual(response['Content-Type'], 'text/xml; charset=utf-8')

    def test_retrieve_xform_manifest_anonymous_user_require_auth(self):
        self.user.profile.require_auth = True
        self.user.profile.save()
        self._load_metadata(self.xform)
        self.view = XFormListApi.as_view({
            "get": "manifest"
        })
        request = self.factory.get('/')
        response = self.view(request, pk=self.xform.pk)
        self.assertEqual(response.status_code, 401)
        response = self.view(request, pk=self.xform.pk,
                             username=self.user.username)
        self.assertEqual(response.status_code, 401)

    def test_retrieve_xform_media(self):
        self._load_metadata(self.xform)
        self.view = XFormListApi.as_view({
            "get": "media"
        })
        request = self.factory.head('/')
        response = self.view(request, pk=self.xform.pk,
                             metadata=self.metadata.pk, format='png')
        auth = DigestAuth('bob', 'bobbob')
        request = self.factory.get('/')
        request.META.update(auth(request.META, response))
        response = self.view(request, pk=self.xform.pk,
                             metadata=self.metadata.pk, format='png')
        self.assertEqual(response.status_code, 200)

    def test_retrieve_xform_media_anonymous_user(self):
        self._load_metadata(self.xform)
        self.view = XFormListApi.as_view({
            "get": "media"
        })
        request = self.factory.get('/')
        response = self.view(request, pk=self.xform.pk,
                             metadata=self.metadata.pk, format='png')
        self.assertEqual(response.status_code, 401)

        response = self.view(request, pk=self.xform.pk,
                             username=self.user.username,
                             metadata=self.metadata.pk, format='png')
        self.assertEqual(response.status_code, 200)

    def test_retrieve_xform_media_anonymous_user_require_auth(self):
        self.user.profile.require_auth = True
        self.user.profile.save()
        self._load_metadata(self.xform)
        self.view = XFormListApi.as_view({
            "get": "media"
        })
        request = self.factory.get('/')
        response = self.view(request, pk=self.xform.pk,
                             metadata=self.metadata.pk, format='png')
        self.assertEqual(response.status_code, 401)
