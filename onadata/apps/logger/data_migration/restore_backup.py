from onadata.apps.logger.models import BackupInstance, BackupXForm, VersionTree
from onadata.apps.logger.models.instance import save_survey
from onadata.apps.logger.models.xform import change_id_string
from .decisioner import MigrationDecisioner, NEW_FIELDS_KEY, RM_FIELDS_KEY, MOD_FIELDS_KEY
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
        changes_list = self._get_migration_changes_in_between(self.xform, self.xform_backup)
        decisions = MigrationDecisioner.convert_changes_to_decisions(
            self._merge_migration_changes(changes_list)
        )
        data_migrator_factory(
            self.xform_backup, self.xform,
            backup_data=False, **decisions
        ).migrate()

    @classmethod
    def _merge_migration_changes(cls, changes_list):
        empty_changes = MigrationDecisioner.construct_changes()
        return cls._merge_migration_changes_aux(changes_list, empty_changes)

    @classmethod
    def _merge_migration_changes_aux(cls, changes_list, merged_changes):
        if not len(changes_list):
            return merged_changes
        changes = changes_list.pop(0)
        new_merged_changes = cls._merge_changes(merged_changes, changes)
        return cls._merge_migration_changes_aux(changes_list, new_merged_changes)

    @classmethod
    def _merge_changes(cls, curr_changes, new_changes):
        merge_and_remove_duplicates = lambda x1, x2: list(set(x1) | set(x2))

        return MigrationDecisioner.construct_changes(
            new=merge_and_remove_duplicates(curr_changes[NEW_FIELDS_KEY],
                                            new_changes[NEW_FIELDS_KEY]),
            removed=merge_and_remove_duplicates(curr_changes[RM_FIELDS_KEY],
                                                new_changes[RM_FIELDS_KEY]),
            modified=cls._transitive_merge(curr_changes[MOD_FIELDS_KEY],
                                           new_changes[MOD_FIELDS_KEY]),
        )

    @staticmethod
    def _transitive_merge(curr_changes, new_changes):
        curr_changes = {
            new_var_name: new_changes.pop(prev_var_name, prev_var_name)
            for new_var_name, prev_var_name in curr_changes.items()
        }
        curr_changes.update(new_changes)
        return curr_changes

    @staticmethod
    def _get_path_in_version_tree(xform, backup):
        return VersionTree.objects.find_path(xform.version_tree, backup.version_tree)

    @classmethod
    def _get_migration_changes_in_between(cls, xform, backup):
        get_migration_changes = lambda vt: vt.version.migration_changes
        path_up, path_down = cls._get_path_in_version_tree(xform, backup)
        path_up_changes = map(cls._rev_changes, map(get_migration_changes, path_up))
        path_down_changes = map(get_migration_changes, path_down)
        return path_up_changes + path_down_changes

    @staticmethod
    def _rev_changes(changes):
        return MigrationDecisioner.reverse_changes(changes)

    def _get_xform_backup(self, version=None, restore_last=False):
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

    @staticmethod
    def _restore_survey_from_backup(survey, backup_survey):
        to_restore = ['xml']
        copy_attrs(backup_survey, survey, to_restore)
        save_survey(survey)
