from django.core.urlresolvers import reverse

from onadata.apps.main.views import edit
from onadata.apps.logger.models import XForm
from test_base import TestBase


class TestFormEdit(TestBase):
    """
    (almost) every option of form edit has been removed from KoBoCAT, except
    media files.
    @ToDo remove skipped (obsolete) tests (or whole class)
    """
    def setUp(self):
        TestBase.setUp(self)
        self._create_user_and_login()
        self._publish_transportation_form_and_submit_instance()
        self.edit_url = reverse(edit, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string
        })

    def test_anon_no_edit_post(self):
        self.xform.shared = True
        self.xform.save()
        desc = 'Snooky'
        response = self.anon.post(self.edit_url, {'description': desc},
                                  HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertNotEqual(
            XForm.objects.get(pk=self.xform.pk).description, desc)
        self.assertEqual(response.status_code, 302)

    def test_not_owner_no_edit_post(self):
        self.xform.shared = True
        self.xform.save()
        desc = 'Snooky'
        self._create_user_and_login("jo")
        response = self.client.post(self.edit_url, {'description': desc},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 403)
        self.assertNotEqual(
            XForm.objects.get(pk=self.xform.pk).description, desc)
