from onadata.apps.logger.models import Instance, XForm, BackupInstance, BackupXForm
from onadata.apps.logger.data_migration.backup_data import backup_xform, backup_survey

from .utils import MigrationTestCase


class BackupSurveysTests(MigrationTestCase):
    def test_backup_xform(self):
        xform_backup = backup_xform(self.xform)
        self.assertEqual(XForm.objects.all().count(), 2)
        self.assertEqual(BackupXForm.objects.all().count(), 1)
        self.assertEqual(xform_backup.xml, self.xform.xml)
        self.assertEqual(xform_backup.user, self.xform.user)

    def test_multiple_xform_backups(self):
        for i in range(10):
            backup_xform(self.xform)
        self.assertEqual(BackupXForm.objects.all().count(), 10)

    def test_backup_survey(self):
        xform_backup = backup_xform(self.xform)
        survey_backup = backup_survey(self.survey, xform_backup)
        self.assertEqual(Instance.objects.all().count(), 1)
        self.assertEqual(BackupInstance.objects.all().count(), 1)
        self.assertEqual(survey_backup.xml, self.survey.xml)
        self.assertEqual(survey_backup.user, self.survey.user)

    def test_multiple_survey_backups(self):
        xform_backup = backup_xform(self.xform)
        for i in range(10):
            backup_survey(self.survey, xform_backup)
        self.assertEqual(BackupInstance.objects.all().count(), 10)
