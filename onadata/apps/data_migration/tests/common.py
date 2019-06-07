import re
from functools import partial

from lxml import etree
from django.test import TestCase
from django.contrib.auth.models import User

from onadata.apps.logger.models import Instance, XForm
from onadata.apps.viewer.models import ParsedInstance
from onadata.apps.data_migration.factories import (
    data_migrator_factory, migration_decisioner_factory
)

from onadata.apps.data_migration.tests import fixtures


def remove_whitespaces(string):
    return re.sub(r"\s+", "", string)


def reduce_whitespaces(string):
    return re.sub(r"\s+", " ", string)


def xmls_not_equal_msg(actual, expected, extra=''):
    return "\n{}!=\n{}. {}".format(actual, expected, extra)


class CommonTestCase(TestCase):
    def assertEqualIgnoringWhitespaces(self, actual, expected):
        self.assertEqual(
            remove_whitespaces(actual),
            remove_whitespaces(expected),
            msg=xmls_not_equal_msg(actual, expected),
        )

    def assertXMLsEqual(self, actual_xml, expected_xml):
        """Assert that given XMLs are equal using string comparison"""
        single_to_double_quotes = lambda s: s.replace("'", '"')
        self.assertEqualIgnoringWhitespaces(
            single_to_double_quotes(actual_xml),
            single_to_double_quotes(expected_xml),
        )

    def assertXMLsIsomorphic(self, actual, expected):
        """Assert that given XMLs are equal up to isomorphism"""
        sort_elems = lambda x: sorted(x, key=lambda e: e.tag)

        def _trees_equal(e1, e2):
            get_msg = lambda e1, e2, attr: (
                "{e1} vs {e2}, {attr}: {e1_attr} != {e2_attr}".format(
                    e1=str(e1), e2=str(e2), attr=attr,
                    e1_attr=getattr(e1, attr), e2_attr=getattr(e2, attr)),
            )
            cmp_tails = lambda e1, e2: (
                remove_whitespaces(e1.tail or '') != remove_whitespaces(e2.tail or '')
            )
            if e1.tag != e2.tag: return False, get_msg(e1, e2, 'tag')
            if e1.text != e2.text: return False, get_msg(e1, e2, 'text')
            if cmp_tails(e1, e2): return False, get_msg(e1, e2, 'tail')
            if e1.attrib != e2.attrib: return False, get_msg(e1, e2, 'attrib')
            if len(e1) != len(e2): return False, "len({}) != len({})".format(str(e1), str(e2))

            for c1, c2 in zip(sort_elems(e1), sort_elems(e2)):
                are_equal, info = _trees_equal(c1, c2)
                if not are_equal:
                    return False, info
            return True, ''

        get_msg = partial(xmls_not_equal_msg, actual, expected)
        actual, expected = reduce_whitespaces(actual), reduce_whitespaces(expected)
        e1, e2 = etree.XML(actual), etree.XML(expected)
        are_equal, info = _trees_equal(e1, e2)
        self.assertTrue(are_equal, msg=get_msg(info))

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


class ThirdMigrationTestCase(MigrationTestCase):
    def get_fixtures(self):
        return {
            'xform': fixtures.form_xml_case_3,
            'xform_new': fixtures.form_xml_case_3_after,
            'survey': fixtures.survey_xml_3,
        }

    def get_migration_decisions(self):
        return {
            'determine_first_name': ['name'],
            'determine_last_name': ['__new_field__'],
            'determine_date': ['__new_field__'],
        }
