from .common import MigrationTestCase, GroupedMigrationTestCase


class MigrationDecisionerUnitTests(MigrationTestCase):
    def setUp(self):
        super(MigrationDecisionerUnitTests, self).setUp()
        self.added = ['birthday', 'first_name']
        self.potentially_removed = ['name']
        self.migration_decisioner = self.create_migration_decisioner()

    def _get_field_changes(self):
        return {
            'new_fields': ['a', 'b', 'c'],
            'removed_fields': ['d', 'e'],
            'modified_fields': {
                'x': 'y',
                'f': 'g',
            },
        }

    def test_extract_migration_decisions(self):
        data = {
            'some': 'not',
            'relevant': 'data',
        }
        data.update(self.migration_decisions)
        expected = {
            key: value[0]
            for key, value in self.migration_decisions.iteritems()
        }
        self.assertEqual(
            self.migration_decisioner._extract_migration_decisions(**data),
            expected
        )

    def test_get_removed_fields(self):
        self.assertEqual(
            self.migration_decisioner.get_removed_fields(
                self.potentially_removed),
            [],
        )

    def test_get_fields_modifications(self):
        self.assertEqual(
            self.migration_decisioner.get_fields_modifications(
                self.potentially_removed),
            {'name': 'first_name'},
        )

    def test_get_new_fields(self):
        self.assertEqual(
            self.migration_decisioner.get_new_fields(self.added),
            ['birthday'],
        )

    def test_get_prepopulate_text(self):
        self.assertEqual(
            self.migration_decisioner.get_prepopulate_text('last_name'),
            'Fowler',
        )

    def test_get_determined_field(self):
        self.assertEqual(
            self.migration_decisioner._get_determined_field('birthday'),
            self.migration_decisioner.NEW_FIELD,
        )

    def test_reverse_changes(self):
        changes = self._get_field_changes()
        expected = {
            'new_fields': ['d', 'e'],
            'removed_fields': ['a', 'b', 'c'],
            'modified_fields': {
                'y': 'x',
                'g': 'f',
            },
        }
        self.assertEqual(
            expected, self.migration_decisioner.reverse_changes(changes),
        )
        expected = {
            'new_fields': ['d', 'e'],
            'removed_fields': ['a', 'b', 'c'],
            'modified_fields': {
                'y': 'x',
                'g': 'f',
            },
        }

    def test_convert_changes_to_decisions(self):
        changes = self._get_field_changes()
        expected = {
            'determine_a': self.migration_decisioner.NEW_FIELD,
            'determine_b': self.migration_decisioner.NEW_FIELD,
            'determine_c': self.migration_decisioner.NEW_FIELD,
            'determine_y': 'x',
            'determine_g': 'f',
        }
        actual = self.migration_decisioner.convert_changes_to_decisions(changes)
        self.assertEqual(expected, actual)

    def test_convert_changes_to_decisions__second_case(self):
        result = self.migration_decisioner.convert_changes_to_decisions(
            self.get_field_changes()
        )
        self.assertEqual({
            'determine_first_name': 'name',
            'determine_birthday': '__new_field__',
            'determine_last_name': '__new_field__',
        }, result)

    def test_prev_fields_groups_migrated(self):
        prev_fields_groups = self.migration_decisioner\
            .prev_fields_groups_migrated()
        self.assertEqual({
          'first_name': [],
          'gender': [],
          'photo': [],
          'age': [],
          'location': [],
        }, prev_fields_groups)

    def test_changed_fields_groups(self):
        changed_fields_groups = self.migration_decisioner\
            .changed_fields_groups()
        self.assertEqual({}, changed_fields_groups)


class GroupedMigrationDecisionerUnitTests(GroupedMigrationTestCase):
    def setUp(self):
        super(GroupedMigrationDecisionerUnitTests, self).setUp()
        self.migration_decisioner = self.create_migration_decisioner()

    def test_changed_fields_groups(self):
        changed_fields_groups = self.migration_decisioner.changed_fields_groups()
        self.assertEqual(
            changed_fields_groups, {
                'isomorphism': ['group_transformations', 'bijective'],
                'automorphism': ['group_transformations', 'bijective'],
                'endomorphism': ['group_transformations'],
            }
        )
