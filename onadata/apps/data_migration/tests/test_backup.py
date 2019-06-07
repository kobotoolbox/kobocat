from onadata.apps.logger.models import Instance
from onadata.apps.data_migration.models import (
        BackupInstance, BackupXForm, XFormVersion)
from onadata.apps.data_migration.backup_data import (
    backup_xform, backup_survey
)
from .common import MigrationTestCase


class BackupSurveysTests(MigrationTestCase):
    def assert_backup_created(self, xform_backup):
        backup = BackupXForm.objects.get(xform_id=self.xform.id).backup_version
        self.assertEqual(self.xform.xml, xform_backup.xml)
        self.assertEqual({
            'Backups': backup,
            'Form user': self.xform.user.id,
        }, {
            'Backups': xform_backup.backup_version,
            'Form user': xform_backup.user.id,
        })

    def test_backup_xform(self):
        xform_backup = backup_xform(self.xform)
        self.assert_backup_created(xform_backup)

    def test_backup_xform__bind(self):
        xform_backup = backup_xform(self.xform, bind=True)
        self.assert_backup_created(xform_backup)
        self.xform.xformversion.refresh_from_db()
        self.assertIsNotNone(self.xform.xformversion.version_tree)
        self.assertEqual(self.xform.xformversion.version_tree.version,
                         xform_backup)

    def test_backup_xform__bind_no_version(self):
        XFormVersion.objects.get(xform=self.xform).delete()
        xform_backup = backup_xform(self.xform, bind=True)
        self.assert_backup_created(xform_backup)
        self.xform.refresh_from_db()
        xf_version = self.xform.xformversion
        self.assertIsNotNone(xf_version)
        self.assertIsNotNone(xf_version.version_tree)
        self.assertEqual(xf_version.version_tree.version, xform_backup)

    def test_backup_xform__bind_twice(self):
        xform_backup1 = backup_xform(self.xform, bind=True)
        xform_backup2 = backup_xform(self.xform, bind=True)
        self.xform.xformversion.refresh_from_db()
        vt = self.xform.xformversion.version_tree
        self.assertIsNotNone(vt)
        self.assertIsNotNone(vt.parent)
        self.assertEqual(vt.parent.version.backup_version,
                         xform_backup1.backup_version)
        self.assertEqual(vt.version.backup_version,
                         xform_backup2.backup_version)

    def test_multiple_xform_backups(self):
        exp = [backup_xform(self.xform).backup_version for _ in range(10)]
        actual = BackupXForm.objects.filter(xform_id=self.xform.id)\
                .values_list('backup_version', flat=True)
        self.assertCountEqual(exp, actual)

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
        exp = [backup_survey(self.survey, xform_backup).date_created
               for i in range(10)]
        actual = BackupInstance.objects.filter(xform__xform_id=self.xform.id).\
            values_list('date_created', flat=True)
        self.assertCountEqual(exp, actual)

    def test_data_migration_creates_proper_version_tree_and_backups(self):
        self.data_migrator.migrate()
        backup_first = BackupXForm.objects.latest_backup(self.xform_new.id)

        self.setup_data_migrator(self.xform_new, self.xform_new)
        self.data_migrator.migrate()
        backup_second = BackupXForm.objects.latest_backup(self.xform_new.id)
        xform_version = self.xform_new.xformversion
        xform_version.refresh_from_db()

        self.assertEqual({
            'Latest backup': xform_version.latest_backup,
            'Older backup': xform_version.version_tree.parent.version,
        }, {
            'Latest backup': backup_second,
            'Older backup': backup_first,
        })
