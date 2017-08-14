from onadata.apps.logger.models import Instance, XForm
from onadata.apps.logger.data_migration.surveytree import SurveyTree
from onadata.apps.logger.models.backup import BackupXForm, BackupInstance

from .utils import MigrationTestCase
from . import fixtures


class DataMigrationUnitTests(MigrationTestCase):
    def setUp(self):
        super(DataMigrationUnitTests, self).setUp()
        self.added = ['birthday', 'first_name']
        self.potentially_removed = ['name']

    def test_migrate_survey(self):
        self.data_migrator.migrate_survey(self.survey)
        survey_tree = SurveyTree(self.survey)
        expected = fixtures.FIELDS[:]
        expected.append('last_name')
        expected.append('birthday')
        expected.remove('date')
        pos = expected.index('name')
        expected[pos] = 'first_name'
        self.assertEqual(survey_tree.get_fields_names(), expected)

    def test_field_prepopulate(self):
        self.data_migrator.migrate_survey(self.survey)
        survey_tree = SurveyTree(self.survey)
        last_name_field = survey_tree.get_field('last_name')
        self.assertEqual(last_name_field.text, 'Fowler')


class DataMigratorIntegrationTests(MigrationTestCase):
    def test_migrator_smoke_test(self):
        # Assure that everything won't break apart after running migrator
        self.data_migrator.migrate()
        self.assertEqual(XForm.objects.all().count(), 2)
        self.assertEqual(BackupXForm.objects.all().count(), 1)
        self.assertEqual(BackupInstance.objects.all().count(), 1)

    def test_survey_migration(self):
        self.data_migrator.migrate()
        self.assertEqual(Instance.objects.all().count(), 1)
        self.assertEqual(self.xform_new.instances.count(), 1)

    def test_migration(self):
        self.data_migrator.migrate()
        self.xform_new.refresh_from_db()
        self.assertEqualIgnoringWhitespaces(
            self.xform_new.instances.first().xml,
            fixtures.survey_after_migration,
        )


class DataMigratorIntegrationSecondTestsCase(MigrationTestCase):
    def setUp(self):
        self.user = self.create_user('alfred_tarski')
        self.xform = self.create_xform(fixtures.form_xml_case_2)
        self.xform_new = self.create_xform(fixtures.form_xml_case_2_after)
        self.survey = self.create_survey(self.xform_new, fixtures.survey_xml_2)
        self.setup_data_migrator(self.xform, self.xform_new)

    def get_migration_decisions(self):
        return {
            'determine_your_name': ['name'],
            'determine_mood': ['__new_field__'],
            'prepopulate_mood': [fixtures.DEFAULT_MOOD],
        }

    def test_migration__second_case(self):
        self.data_migrator.migrate()
        self.xform.refresh_from_db()
        self.xform_new.refresh_from_db()
        self.assertEqualIgnoringWhitespaces(
            self.xform_new.xml,
            fixtures.form_xml_case_2_after,
        )
        self.assertEqualIgnoringWhitespaces(
            self.xform_new.instances.first().xml,
            fixtures.survey_2_after_migration,
        )
