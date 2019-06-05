from onadata.apps.logger.models import Instance, XForm
from onadata.apps.data_migration.surveytree import SurveyTree
from onadata.apps.data_migration.models.backup import BackupXForm, BackupInstance

from onadata.apps.data_migration.tests import common as test_case, fixtures


class DataMigrationUnitTests(test_case.MigrationTestCase):
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
        pos = expected.index('name')
        expected[pos] = 'first_name'
        self.assertCountEqual(expected, survey_tree.get_fields_names())

    def test_field_prepopulate(self):
        self.data_migrator.migrate_survey(self.survey)
        survey_tree = SurveyTree(self.survey)
        last_name_field = survey_tree.get_field('last_name')
        self.assertEqual(last_name_field.text, 'Fowler')


class DataMigratorIntegrationTests(test_case.MigrationTestCase):
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


class DataMigratorIntegrationSecondTestsCase(test_case.SecondMigrationTestCase):
    def test_migration__second_case(self):
        self.data_migrator.migrate()
        self.xform_new.refresh_from_db()
        self.assertEqualIgnoringWhitespaces(
            self.xform_new.xml,
            fixtures.form_xml_case_2_after,
        )
        self.assertEqualIgnoringWhitespaces(
            self.xform_new.instances.first().xml,
            fixtures.survey_2_after_migration,
        )


class DataMigratorIntegrationBasicGroupsTestCase(test_case.BasicGroupedMigrationTestCase):
    def test_migration__basic_grouped_case(self):
        self.data_migrator.migrate()
        self.xform_new.refresh_from_db()
        self.assertEqualIgnoringWhitespaces(
            self.xform_new.xml,
            fixtures.form_xml_groups_after,
        )
        self.assertEqualIgnoringWhitespaces(
            self.xform_new.instances.first().xml,
            fixtures.survey_xml_groups_after,
        )


class DataMigratorIntegrationGroupsTestCase(test_case.GroupedMigrationTestCase):
    def test_migration__grouped_case(self):
        self.data_migrator.migrate()
        self.xform_new.refresh_from_db()
        self.assertEqualIgnoringWhitespaces(
            self.xform_new.xml,
            fixtures.form_xml_groups_after__second,
        )
        self.assertEqualIgnoringWhitespaces(
            self.xform_new.instances.first().xml,
            fixtures.survey_xml_groups_after__second,
        )


class DataMigratorIntegrationSecondTestsCase(test_case.ThirdMigrationTestCase):
    def test_migration__third_case(self):
        self.data_migrator.migrate()
        self.xform_new.refresh_from_db()
        self.assertEqualIgnoringWhitespaces(
            self.xform_new.xml,
            fixtures.form_xml_case_3_after,
        )
        self.assertEqualIgnoringWhitespaces(
            self.xform_new.instances.first().xml,
            fixtures.survey_3_after_migration,
        )
