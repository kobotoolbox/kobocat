from unittest import skip
from mock import patch

from django.test import Client
from django.core.urlresolvers import reverse

from onadata.apps.logger.models import Instance, XForm

from .common import MigrationTestCase


class MigrationViewsTests(MigrationTestCase):
    def setUp(self):
        super(MigrationViewsTests, self).setUp()
        self.client = Client()
        self.client.login(username=self.user.username,
                          password='password')

    def get_data__both_id_strings(self):
        return {
            'username': self.user.username,
            'old_id_string': self.xform.id_string,
            'new_id_string': self.xform_new.id_string,
        }

    def get_data__one_id_string(self, xform):
        return {
            'username': self.user.username,
            'id_string': xform.id_string,
        }

    def test_xform_migration_gui(self):
        url = reverse('xform-migration-gui',
                      kwargs=self.get_data__both_id_strings())
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.xform_new.id_string, response.content)
        self.assertIn('Data migration', response.content)
        self.assertIn('birthday', response.content)

    def test_abandon_xform_data_migration(self):
        url = reverse('abandon-xform-data-migration',
                      kwargs=self.get_data__both_id_strings())
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(XForm.objects.count(), 1)
        self.assertEqual(self.xform_new.instances.count(), 1)
        self.assertEqual(Instance.objects.count(), 1)

    def test_abandon_xform_data_migration_other_user(self):
        user2 = self.create_user('user2')
        self.client.login(username=user2.username,
                          password='password')
        url = reverse('abandon-xform-data-migration',
                      kwargs=self.get_data__both_id_strings())
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(XForm.objects.count(), 2)

    @skip("intented to be fixed in the next PR")
    def test_migrate_xform_data(self):
        url = reverse('migrate-xform-data',
                      kwargs=self.get_data__both_id_strings())
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(XForm.objects.count(), 1)
        self.assertEqual(Instance.objects.count(), 1)

    def test_update_xform_and_prepare_migration(self):
        url = reverse('update-xform-and-prepare-migration',
                      kwargs=self.get_data__one_id_string(self.xform_new))
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(XForm.objects.count(), 2)
        self.assertEqual(Instance.objects.count(), 1)

    def test_migration_process(self):
        url = reverse('update-xform-and-prepare-migration',
                      kwargs=self.get_data__one_id_string(self.xform))
        self.client.post(url)
        url = reverse('migrate-xform-data',
                      kwargs=self.get_data__both_id_strings())
        response = self.client.post(url, self.get_migration_decisions())
        self.assertEqual(response.status_code,  302)
        self.assertEqual(XForm.objects.count(), 1)
        self.assertEqual(Instance.objects.count(), 1)

    @patch('onadata.apps.data_migration.restore_backup.BackupRestorer._get_xform_backup')  # noqa
    @patch('onadata.apps.data_migration.restore_backup.BackupRestorer.restore_xform_backup')  # noqa
    def test_restore_backup_view(self, restore_backup_mock, *args):
        url = reverse('restore-backup',
                      kwargs=self.get_data__one_id_string(self.xform_new))
        response = self.client.post(url, {'restore_last': True})

        restore_backup_mock.assert_called_once()
        self.assertEqual(response.status_code,  200)
