from onadata.apps.logger.models.backup import BackupInstance, BackupXForm
from onadata.apps.logger.models.instance import save_survey
from onadata.apps.logger.models.xform import change_id_string

from .decisioner import MigrationDecisioner
from .factories import data_migrator_factory


class BackupRestoreError(Exception):
    pass


def copy_attrs(from_obj, to_obj, attrs):
    for attr in attrs:
        new_value = getattr(from_obj, attr)
        setattr(to_obj, attr, new_value)


class BackupRestorer(object):
    def __init__(self, xform, version=None, restore_last=False):
        self.xform = xform
        self.xform_backup = self._get_xform_backup(version, restore_last)

    def restore_xform_backup(self):
        self._restore_xform_from_backup()

        for survey in self.xform.instances.iterator():
            try:
                backup_survey = self.xform_backup.surveys.get(uuid=survey.uuid)
            except BackupInstance.DoesNotExist:
                self.migrate_survey_to_prev_schema(survey)
            else:
                self._restore_survey_from_backup(survey, backup_survey)

    def migrate_survey_to_prev_schema(self, survey):
        changes = self.xform_backup.changes
        reversed_decisions = self.get_reversed_migration_decisions(changes)
        data_migrator_factory(
            self.xform_backup, self.xform,
            backup_data=False, **reversed_decisions
        ).migrate()

    @staticmethod
    def get_reversed_migration_decisions(changes):
        reversed_changes = MigrationDecisioner.reverse_changes(changes)
        return MigrationDecisioner.convert_changes_to_decisions(reversed_changes)

    def _get_xform_backup(self, version, restore_last):
        if bool(version) == bool(restore_last):
            raise BackupRestoreError('Could not restore backup. Need to provide '
                                     'either backup version or restore last')

        if restore_last:
            return BackupXForm.objects.latest_backup(self.xform.id)
        try:
            return BackupXForm.objects.get(backup_version=version,
                                           xform_id=self.xform.id)
        except BackupXForm.DoesNotExist:
            raise BackupRestoreError('The following backup version does not '
                                     'exist: {}'.format(version))

    def _restore_xform_from_backup(self):
        to_restore = ['xls', 'xml', 'description']
        copy_attrs(self.xform_backup, self.xform, to_restore)
        change_id_string(self.xform, self.xform.id_string)
        self.xform.save()

    def _restore_survey_from_backup(self, survey, backup_survey):
        to_restore = ['xml']
        copy_attrs(backup_survey, survey, to_restore)
        save_survey(survey)
