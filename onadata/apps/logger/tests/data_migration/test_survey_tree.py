from lxml import etree

from django.test import TestCase

from onadata.apps.logger.data_migration.surveytree import (
    SurveyTree, MissingFieldException
)
from . import fixtures


class SurveyTreeOperationsTest(TestCase):
    def setUp(self):
        super(SurveyTreeOperationsTest, self).setUp()
        self.survey = SurveyTree(fixtures.survey_xml)

    def test_get_fields_name(self):
        self.assertEqual(
            self.survey.get_fields_names(),
            fixtures.FIELDS
        )

    def test_get_fields(self):
        for field in self.survey.get_fields():
            self.assertTrue(etree.iselement(field))

    def test_get_field(self):
        self.assertTrue(etree.iselement(self.survey.get_field('name')))
        self.assertTrue(etree.iselement(self.survey.get_field('photo')))

    def test_get_field__no_such_field(self):
        with self.assertRaises(MissingFieldException):
            self.survey.get_field('i_am_sure_no_such_field_exist')

    def test_create_element(self):
        self.assertTrue(etree.iselement(self.survey.create_element('name')))

    def test_permanently_remove_field(self):
        expected = fixtures.FIELDS[:]
        expected.remove('name')
        self.survey.permanently_remove_field('name')
        self.assertEqual(self.survey.get_fields_names(), expected)

    def test_modify_field(self):
        expected = fixtures.FIELDS[:]
        pos = expected.index('name')
        expected[pos] = 'first_name'
        self.survey.modify_field('name', 'first_name')
        self.assertEqual(self.survey.get_fields_names(), expected)

    def test_add_field(self):
        expected = fixtures.FIELDS[:]
        expected.append('opinion')
        self.survey.add_field('opinion')
        self.assertEqual(self.survey.get_fields_names(), expected)

    def test_add_field__should_add_if_already_exist(self):
        self.survey.add_field('name')
        self.assertEqual(self.survey.get_fields_names(), fixtures.FIELDS[:])


class SurveyTreeWithGroupsOperationsTest(TestCase):
    def setUp(self):
        super(SurveyTreeWithGroupsOperationsTest, self).setUp()
        self.survey = SurveyTree(fixtures.survey_xml_groups_after__second)

    def test_get_group(self):
        self.assertTrue(etree.iselement(self.survey.find_group('bijective')))
        self.assertTrue(etree.iselement(self.survey.find_group(
            'group_transformations'
        )))

    def test_get_group__raises_on_normal_field(self):
        with self.assertRaises(MissingFieldException):
            self.survey.find_group('isomorphism')

    def test_get_group__raises_on_no_such_group(self):
        with self.assertRaises(MissingFieldException):
            self.survey.find_group('certainly_no_such_group_exist')

    def test_insert_field_into_group_chain(self):
        # TODO: write test
        pass
