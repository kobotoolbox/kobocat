from onadata.apps.logger.data_migration.factories import migration_decisioner_factory

from .utils import MigrationTestCase


class MigrationDecisionerUnitTests(MigrationTestCase):
    def setUp(self):
        super(MigrationDecisionerUnitTests, self).setUp()
        self.added = ['birthday', 'first_name']
        self.potentially_removed = ['name']
        self.migration_decisioner = migration_decisioner_factory(
            self.xform, self.xform_new, **self.migration_decisions)

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
