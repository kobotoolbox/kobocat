from onadata.apps.logger.models import Instance, BackupInstance, BackupXForm
from onadata.apps.logger.data_migration.backup_data import (
    create_xform_backup, backup_xform, backup_survey
)
from .common import MigrationTestCase


class BackupSurveysTests(MigrationTestCase):
    def test_backup_xform(self):
        BackupXForm.objects.all().delete()
        xform_backup = backup_xform(self.xform)
        self.assertEqual(self.xform.xml, xform_backup.xml)
        self.assertEqual({
            'Backups': BackupXForm.objects.first().backup_version,
            'Form user': self.xform.user.id,
        }, {
            'Backups': xform_backup.backup_version,
            'Form user': xform_backup.user.id,
        })

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

    def test_data_migration_creates_proper_version_tree_and_backups(self):
        self.data_migrator.migrate()
        backup_first = BackupXForm.objects.latest_backup(self.xform_new.id)

        self.setup_data_migrator(self.xform_new, self.xform_new)
        self.data_migrator.migrate()
        backup_second = BackupXForm.objects.latest_backup(self.xform_new.id)

        self.assertEqual({
            'Latest backup': self.xform_new.latest_backup,
            'Older backup': self.xform_new.version_tree.parent.version,
        }, {
            'Latest backup': backup_second,
            'Older backup': backup_first,
        })
