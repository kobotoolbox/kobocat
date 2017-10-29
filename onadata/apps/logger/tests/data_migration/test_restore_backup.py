from datetime import datetime

from onadata.apps.logger.models import VersionTree
from onadata.apps.logger.data_migration.decisioner import MigrationDecisioner
from onadata.apps.logger.data_migration.backup_data import create_xform_backup, backup_xform
from onadata.apps.logger.data_migration.restore_backup import (
    copy_attrs, BackupRestorer, BackupRestoreError
)

from .common import MigrationTestCase, SecondMigrationTestCase
from . import fixtures


class CommonBackupRestoreTestCase(MigrationTestCase):
    def _migrate_and_restore(self, version=None, restore_last=False):
        self.data_migrator.migrate()
        restorer = BackupRestorer(self.xform_new, version, restore_last)
        restorer.restore_xform_backup()
        return restorer

    def _construct_changes(self, new=None, removed=None, modified=None):
        return MigrationDecisioner.construct_changes(new, removed, modified)


class BackupRestoreTestCase(CommonBackupRestoreTestCase):
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
        """Test if migration composed with restore is identity"""
        self._migrate_and_restore(restore_last=True)
        self.assertXMLsEqual(
            self.xform_new.xml,
            fixtures.form_xml_case_1.replace('Survey', 'Survey2'),
        )
        self.assertEqualIgnoringWhitespaces(
            self.xform_new.instances.first().xml,
            fixtures.survey_xml,
        )

    def test_migrate_survey_to_prev_schema(self):
        restorer = self._migrate_and_restore(restore_last=True)
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
        restorer_backup = restorer._get_xform_backup(restore_last=True).id
        self.assertEqual(restorer_backup, backup.id)

    def test_get_xform_backup__from_version(self):
        date = datetime(2017, 1, 1, 1)
        backup = create_xform_backup(self.xform_new,
                                     changes=self.get_field_changes())
        create_xform_backup(self.xform_new,
                            changes=self.get_field_changes())
        create_xform_backup(self.xform_new,
                            changes=self.get_field_changes())
        backup.backup_version = date
        backup.save()
        restorer = BackupRestorer(self.xform_new, version=date)
        self.assertEqual(backup.id, restorer.xform_backup.id)

    def test_transitive_merge(self):
        curr_changes = {
            'x': 'y',
            'p': 'q'
        }
        new_changes = {
            'y': 'z',
            'f': 'g',
        }
        expected = {'x': 'z', 'p': 'q', 'f': 'g'}
        self.assertEqual(BackupRestorer._transitive_merge(curr_changes, new_changes), expected)

    def test_transitive_merge__handle_empty_dict(self):
        changes = {'f': 'g'}
        self.assertEqual(BackupRestorer._transitive_merge({}, changes), changes)

    def test_merge_changes(self):
        curr_changes = self._construct_changes(
            new=['age', 'birthday'],
            removed=[],
            modified={'x': 'y'},
        )
        new_changes = self._construct_changes(
            new=['mood'],
            removed=['coolness'],
            modified={'y': 'z'},
        )
        expected = self._construct_changes(
            new=['age', 'birthday', 'mood'],
            removed=['coolness'],
            modified={'x': 'z'},
        )
        self.assertEqual(BackupRestorer._merge_changes(curr_changes, new_changes), expected)

    def test_merge_migration_changes(self):
        changes_list = map(lambda d: self._construct_changes(**d), [{
            'new': [],
            'removed': [],
            'modified': {'f': 'g'},
        }, {
            'new': ['a', 'b'],
            'removed': ['v'],
            'modified': {'g': 'h', 'x': 'y'},
        }, {
            'new': ['c'],
            'removed': ['v'],
            'modified': {'h': 'q'},
        }, {
            # Expected result
            'new': ['a', 'c', 'b'],
            'removed': ['v'],
            'modified': {'f': 'q', 'x': 'y'}
        }])
        expected = changes_list.pop()
        self.assertEqual(expected, BackupRestorer._merge_migration_changes(changes_list))

    def test_merge_migration_changes__second(self):
        result = BackupRestorer._merge_migration_changes([
            self._construct_changes([], ['name'], {'g': 'f'}),
            self._construct_changes([], ['mood'], {'f': 'h'}),
        ])
        self.assertEqual(result, self._construct_changes(
            new=[], removed=['name', 'mood'], modified={'g': 'h'},
        ))

    def test_migration_changes_between_two_version_trees(self):
        initial_changes = self._construct_changes(['age'])
        changes_fst = self._construct_changes([], ['mood'], {'f': 'h'})
        changes_snd = self._construct_changes(['name'], [], {'f': 'g'})

        backup_xform(self.xform, migration_changes=initial_changes, bind=True)
        backup_to_restore = backup_xform(self.xform, migration_changes=changes_fst, bind=True)

        current_backup = backup_xform(self.xform, migration_changes=changes_snd, bind=False)
        vt = VersionTree.objects.create(parent=self.xform.version_tree.parent,
                                        version=current_backup)
        self.xform.version_tree = vt
        self.xform.save()

        result = BackupRestorer._get_migration_changes_in_between(self.xform, backup_to_restore)
        self.assertEqual([
            self._construct_changes([], ['name'], {'g': 'f'}),
            self._construct_changes([], ['mood'], {'f': 'h'}),
        ], result)


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
