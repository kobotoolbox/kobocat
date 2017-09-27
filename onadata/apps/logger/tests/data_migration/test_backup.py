from datetime import datetime

from onadata.apps.logger.models import Instance, XForm, BackupInstance, BackupXForm
from onadata.apps.logger.data_migration.backup_data import (
    create_xform_backup, backup_xform, backup_survey
)
from onadata.apps.logger.data_migration.restore_backup import (
    copy_attrs, BackupRestorer, BackupRestoreError
)

from .common import MigrationTestCase, SecondMigrationTestCase
from . import fixtures


class BackupSurveysTests(MigrationTestCase):
    def test_backup_xform(self):
        BackupXForm.objects.all().delete()
        xform_backup = backup_xform(self.xform)
        sorting_key = lambda x: x.title
        self.assertEqual(xform_backup.xml, self.xform.xml)
        self.assertEqual({
            'XForms': sorted(XForm.objects.all(), key=sorting_key),
            'Num of backups': BackupXForm.objects.all().count(),
            'Backup user': xform_backup.user,
        }, {
            'XForms': sorted([self.xform, self.xform_new], key=sorting_key),
            'Num of backups': 1,
            'Backup user': self.xform.user,
        })

    def test_backup_xform_takes_latest_migration_changes(self):
        create_xform_backup(self.xform_new, changes={'some': 'changes'})
        backup1 = create_xform_backup(self.xform_new,
                                      changes=self.get_field_changes())
        backup2 = create_xform_backup(self.xform_new)
        self.assertEqual(backup1.migration_changes, backup2.migration_changes)

    def test_multiple_xform_backups(self):
        BackupXForm.objects.all().delete()
        for i in range(10):
            backup_xform(self.xform)
        self.assertEqual(BackupXForm.objects.all().count(), 10)

    def test_backup_survey(self):
        xform_backup = backup_xform(self.xform)
        survey_backup = backup_survey(self.survey, xform_backup)
        self.assertEqual(survey_backup.xml, self.survey.xml)
        self.assertEqual({
            'Number of instances': Instance.objects.all().count(),
            'Backup instances': BackupInstance.objects.all().count(),
            'Survey backup user': survey_backup.user,
        }, {
            'Number of instances': 1,
            'Backup instances': 1,
            'Survey backup user': self.survey.user,
        })

    def test_multiple_survey_backups(self):
        xform_backup = backup_xform(self.xform)
        for i in range(10):
            backup_survey(self.survey, xform_backup)
        self.assertEqual(BackupInstance.objects.all().count(), 10)


class CommonBackupRestoreTestCase(object):
    def _migrate_and_restore(self, version=None, restore_last=False):
        self.data_migrator.migrate()
        restorer = BackupRestorer(self.xform_new, version, restore_last)
        restorer.restore_xform_backup()
        return restorer


class BackupRestoreTestCase(CommonBackupRestoreTestCase):
    def setUp(self):
        super(BackupRestoreTestCase, self).setUp()

    def test_copy_attrs(self):
        class Dummy:
            pass

        d1 = Dummy()
        d2 = Dummy()

        d1.x = 'should-be-overriden'
        d2.x = 'new-x-value'
        d2.y = 'y-value'

        copy_attrs(d2, d1, ['x', 'y'])

        self.assertEqual(
            {'d1.x': d1.x, 'd1.y': d1.y},
            {'d1.x': 'new-x-value', 'd1.y': 'y-value'}
        )

    def test_restoring_last_backup(self):
        self._migrate_and_restore(restore_last=True)
        self.assertEqualIgnoringWhitespaces(
            self.xform_new.xml,
            fixtures.form_xml_case_1,
        )
        self.assertEqualIgnoringWhitespaces(
            self.xform_new.instances.first().xml,
            fixtures.survey,
        )

    def test_migrate_survey_to_prev_schema(self):
        restorer = self._migrate_and_restore()
        survey = self.create_survey(
            xform=self.xform_new, xml=fixtures.survey_after_migration
        )
        restorer.migrate_survey_to_prev_schema(survey)
        self.assertEqualIgnoringWhitespaces(
            self.survey.xml,
            fixtures.survey_xml,
        )

    def test_get_xform_backup__should_fail_when_providing_both(self):
        version = datetime.now()
        restore_last = True
        with self.assertRaises(BackupRestoreError):
            BackupRestorer(self.xform_new, version, restore_last)

    def test_get_xform_backup__should_fail_when_providing_none(self):
        with self.assertRaises(BackupRestoreError):
            BackupRestorer(self.xform_new)

    def test_get_xform_backup(self):
        restorer = BackupRestorer(self.xform_new, restore_last=True)
        backup = create_xform_backup(self.xform_new,
                                     changes=self.get_field_changes())
        self.assertEqual(backup.id, restorer.xform_backup.id)

    def test_get_xform_backup__from_version(self):
        date = datetime.datetime(2017, 1, 1, 1)
        backup = create_xform_backup(self.xform_new,
                                     changes=self.get_field_changes())
        create_xform_backup(self.xform_new,
                            changes=self.get_field_changes())
        create_xform_backup(self.xform_new,
                            changes=self.get_field_changes())
        backup.backup_version = date
        restorer = BackupRestorer(self.xform_new, version=date)
        self.assertEqual(backup.id, restorer.xform_backup.id)


class BackupRestoreSecondTestCase(CommonBackupRestoreTestCase,
                                  SecondMigrationTestCase):
    def test_restoring_last_backup(self):
        self._migrate_and_restore(restore_last=True)
        self.assertXMLsEqual(
            self.xform_new.xml,
            fixtures.form_xml_case_2.replace('tutorial', 'tutorial2'),
        )
        self.assertEqualIgnoringWhitespaces(
            self.xform_new.instances.first().xml,
            fixtures.survey_xml_2,
        )
