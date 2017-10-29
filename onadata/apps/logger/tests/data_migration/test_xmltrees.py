from lxml import etree

from django.test import TestCase

from onadata.apps.logger.data_migration.xformtree import XFormTree
from onadata.apps.logger.data_migration.surveytree import SurveyTree

from . import fixtures


class XFormTreeOperationsTestCase(TestCase):
    def setUp(self):
        self.prev_tree = XFormTree(fixtures.form_xml_case_1)
        self.new_tree = XFormTree(fixtures.form_xml_case_1_after)

    def test_create_tree(self):
        self.assertTrue(etree.iselement(self.prev_tree.root))
        self.assertTrue(etree.iselement(self.new_tree.root))
        self.assertEqual(self.prev_tree.clean_tag(self.prev_tree.root.tag), 'html')

    def test_get_titles(self):
        self.assertEqual(
            (self.prev_tree.get_title(), self.new_tree.get_title()),
            ('Survey', 'Survey2'))

    def test_get_heads_instance(self):
        self.assertEqual(
            self.prev_tree.clean_tag(
                self.prev_tree.get_head_instance().tag), 'Survey'
        )

    def test_get_fields(self):
        expected1 = ['name',  'gender',  'photo',  'age',  'date',  'location']
        expected2 = [
            'first_name', 'last_name', 'birthday',
            'gender',  'photo',  'age',  'location'
        ]
        self.assertEqual(
            (self.prev_tree.get_fields(), self.new_tree.get_fields()),
            (expected1, expected2)
        )

    def test_get_fields_types(self):
        self.assertDictContainsSubset(
            {'name': 'string', 'location': 'geopoint'},
            self.prev_tree.get_fields_types()
        )

    def test_get_inputs_as_dict(self):
        self.assertDictContainsSubset(
            {'name': self.prev_tree.get_body_content()[0].getchildren()},
            self.prev_tree.get_inputs_as_dict()
        )

    def test_get_cleaned_nodeset(self):
        self.assertEqual(
            self.prev_tree.get_cleaned_nodeset(
                self.prev_tree.get_binds()[0]), 'name'
        )

    def test_get_input_name(self):
        self.assertEqual(
            self.prev_tree.get_input_name(
                self.prev_tree.get_body_content()[0]), 'name',
        )

    def test_find_element_in_tree(self):
        searched_tag = self.prev_tree.get_head_instance().tag
        element = self.prev_tree.find_element_in_tree(searched_tag)
        self.assertTrue(etree.iselement(element))
        self.assertEqual(element.tag, searched_tag)

    def test_find_element_in_tree_by_cleaned_tag(self):
        searched_tag = 'gender'
        element = self.prev_tree.find_element_in_tree(searched_tag)
        self.assertTrue(etree.iselement(element))
        self.assertEqual(self.prev_tree.clean_tag(element.tag), searched_tag)

    def test_not_finding_element_in_tree(self):
        element = self.prev_tree.find_element_in_tree('definitely_not_here')
        self.assertEqual(element, None)

    def test_to_string(self):
        self.assertTrue(self.prev_tree.to_string())

    def test_set_tag(self):
        tag_name = self.prev_tree.get_head_instance().tag
        new_tag_name = 'Survey2'
        self.prev_tree.set_tag(tag_name, new_tag_name)
        self.assertEqual(
            self.prev_tree.clean_tag(self.prev_tree.get_head_instance().tag),
            new_tag_name
        )


class SurveyTreeOperationsTest(TestCase):
    def setUp(self):
        self.survey = SurveyTree(fixtures.survey_xml)

    def test_get_fields_names(self):
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

    def test_create_element(self):
        self.assertTrue(etree.iselement(self.survey.create_element('name')))

    def test_permamently_remove_field(self):
        expected = fixtures.FIELDS[:]
        expected.remove('name')
        self.survey.permamently_remove_field('name')
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
