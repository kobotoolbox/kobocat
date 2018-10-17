"""
Tool for restoring backups

In order to provide flexibility in xform versions, after each update of the
form we create a backup, both of the schema and the data. You may restore
form to previous version and then continue with updating, thus, a version
tree (logger.models.VersionTree) is needed in order to track all changes.

While restoring the backup from version X, we look for the path in tree from
current form, to the X version, and we transitively merge together all of the
schema changes that occurred in that path. Then we used this merged schema
to transition in one step from current state to version X. The transition
is achieved using the very same tool that we use to upgrade the form.
"""
from onadata.apps.data_migration.models import BackupXForm, VersionTree
from onadata.apps.data_migration.models.version import change_id_string
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
        self.old_xml = self.xform.xml
        self.xform_backup = self._get_xform_backup(version, restore_last)

    def restore_xform_backup(self):
        self._restore_xform_from_backup()
        self.migrate_surveys_to_prev_schema()

    def migrate_surveys_to_prev_schema(self):
        changes_list = self._get_migration_changes_in_between(self.xform, self.xform_backup)
        decisions = MigrationDecisioner.convert_changes_to_decisions(
            self._merge_migration_changes(changes_list)
        )
        data_migrator_factory(
            self.xform_backup, self.xform, backup_data=False,
            xml_replacement=self.old_xml, **decisions
        ).migrate()

    @classmethod
    def _merge_migration_changes(cls, changes_list):
        return reduce(
            cls._merge_changes,
            changes_list,
            MigrationDecisioner.construct_changes()
        )

    @classmethod
    def _merge_changes(cls, curr_changes, new_changes):
        merge_and_remove_duplicates = lambda x1, x2: list(set(x1) | set(x2))

        return MigrationDecisioner.construct_changes(
            new=merge_and_remove_duplicates(curr_changes[MigrationDecisioner.NEW_FIELDS_KEY],
                                            new_changes[MigrationDecisioner.NEW_FIELDS_KEY]),
            removed=merge_and_remove_duplicates(curr_changes[MigrationDecisioner.RM_FIELDS_KEY],
                                                new_changes[MigrationDecisioner.RM_FIELDS_KEY]),
            modified=cls._transitive_merge(curr_changes[MigrationDecisioner.MOD_FIELDS_KEY],
                                           new_changes[MigrationDecisioner.MOD_FIELDS_KEY]),
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
        return VersionTree.objects.find_path(
            xform.xformversion.version_tree, backup.version_tree)

    @classmethod
    def _get_migration_changes_in_between(cls, xform, backup):
        path_up, path_down = cls._get_path_in_version_tree(xform, backup)
        path_up_changes = map(MigrationDecisioner.reverse_changes,
                              cls._get_changes_from_vt_path(path_up))
        path_down_changes = cls._get_changes_from_vt_path(path_down)
        return path_up_changes + path_down_changes

    @staticmethod
    def _get_changes_from_vt_path(path):
        return map(lambda vt: vt.version.migration_changes, path)

    def _get_xform_backup(self, version=None, restore_last=False):
        if bool(version) == bool(restore_last):
            raise BackupRestoreError('Could not restore backup. Need to provide '
                                     'either backup version or restore last')

        if restore_last:
            return self.xform.xformversion.latest_backup
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
