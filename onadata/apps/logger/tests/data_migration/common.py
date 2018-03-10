from django.test import TestCase
from django.contrib.auth.models import User

from onadata.apps.logger.models import Instance, XForm
from onadata.apps.viewer.models import ParsedInstance
from onadata.apps.logger.data_migration.factories import (
    data_migrator_factory, migration_decisioner_factory
)

from . import fixtures


def remove_whitespaces(string):
    return string.replace('\n', '').replace(' ', '')


class CommonTestCase(TestCase):
    def assertEqualIgnoringWhitespaces(self, result, expected):
        self.assertEqual(
            remove_whitespaces(result),
            remove_whitespaces(expected),
        )

    def assertXMLsEqual(self, result_xml, expected_xml):
        single_to_double_quotes = lambda s: s.replace("'", '"')
        self.assertEqualIgnoringWhitespaces(
            single_to_double_quotes(result_xml),
            single_to_double_quotes(expected_xml),
        )

    def assertCountEqual(self, expected, actual):
        self.assertEqual(sorted(expected), sorted(actual))

    def create_user(self, username):
        return User.objects.create_user(username=username,
                                        password='password')

    def create_xform(self, xml):
        return XForm.objects.create(
            xml=xml,
            user=self.user
        )

    def create_survey(self, xform, xml=fixtures.survey_xml):
        survey = Instance.objects.create(xml=xml, user=self.user, xform=xform)
        survey.parsed_instance = ParsedInstance.objects.create(instance=survey)
        return survey


class MigrationTestCase(CommonTestCase):
    def get_fixtures(self):
        return {
            'xform': fixtures.form_xml_case_1,
            'xform_new': fixtures.form_xml_case_1_after,
            'survey': fixtures.survey_xml,
        }

    def setUp(self):
        self.user = self.create_user('johnny_cash')
        xml_fixtures = self.get_fixtures()
        self.xform = self.create_xform(xml_fixtures['xform'])
        self.xform_new = self.create_xform(xml_fixtures['xform_new'])
        self.survey = self.create_survey(self.xform_new, xml_fixtures['survey'])
        self.setup_data_migrator(self.xform, self.xform_new)

    def setup_data_migrator(self, xform, xform_new, decisions=None):
        self.migration_decisions = decisions or self.get_migration_decisions()
        self.data_migrator = data_migrator_factory(xform, xform_new,
                                                   **self.migration_decisions)

    def create_migration_decisioner(self):
        return migration_decisioner_factory(self.xform, self.xform_new,
                                            **self.migration_decisions)

    def get_migration_decisions(self):
        return {
            'prepopulate_last_name': ['Fowler'],
            'determine_first_name': ['name'],
            'determine_birthday': ['__new_field__'],
            'determine_last_name': ['__new_field__'],
        }

    def get_field_changes(self):
        return {
            'new_fields': ['birthday', 'last_name'],
            'removed_fields': ['date'],
            'modified_fields': {
                'name': 'first_name',
            },
        }


class SecondMigrationTestCase(MigrationTestCase):
    def get_fixtures(self):
        return {
            'xform': fixtures.form_xml_case_2,
            'xform_new': fixtures.form_xml_case_2_after,
            'survey': fixtures.survey_xml_2,
        }

    def get_migration_decisions(self):
        return {
            'determine_your_name': ['name'],
            'determine_mood': ['__new_field__'],
            'prepopulate_mood': [fixtures.DEFAULT_MOOD],
        }


class BasicGroupedMigrationTestCase(MigrationTestCase):
    def get_fixtures(self):
        return {
            'xform': fixtures.form_xml_groups_before,
            'xform_new': fixtures.form_xml_groups_after,
            'survey': fixtures.survey_xml_groups_before,
        }

    def get_migration_decisions(self):
        return {
            'determine_isomorphism': ['isooomorphism']
        }


class GroupedMigrationTestCase(MigrationTestCase):
    def get_fixtures(self):
        return {
            'xform': fixtures.form_xml_groups_before__second,
            'xform_new': fixtures.form_xml_groups_after__second,
            'survey': fixtures.survey_xml_groups_before__second,
        }

    def get_migration_decisions(self):
        return {
            'determine_homeomorphism': ['__new_field__'],
        }
