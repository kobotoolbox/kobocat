from lxml import etree

from django.test import TestCase

from onadata.apps.data_migration.xformtree import XFormTree
from .common import CommonTestCase
from onadata.apps.data_migration.tests import fixtures


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
        expected1 = ['name', 'gender', 'photo', 'age', 'date', 'location']
        expected2 = [
            'first_name', 'last_name', 'birthday',
            'gender', 'photo', 'age', 'location'
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


class XFormTreeGroupsOperationsTestCase(CommonTestCase):
    def setUp(self):
        self.prev_tree = XFormTree(fixtures.form_xml_groups_before__second)
        self.new_tree = XFormTree(fixtures.form_xml_groups_after__second)

    @staticmethod
    def get_all_fields():
        return ['start', 'end', 'isomorphism', 'current_date',
                'endomorphism', 'math_degree', 'automorphism']

    def test_get_groups(self):
        get_tags = lambda xs: map(lambda x: self.new_tree.clean_tag(x.tag), xs)
        groups = ['bijective', 'group_transformations', 'continuous']
        self.assertCountEqual(get_tags(self.new_tree.get_groups()), groups)
        self.assertEqual(self.prev_tree.get_groups(), [])

    def test_get_fields(self):
        expected_prev = sorted(self.get_all_fields())
        expected_new = sorted(expected_prev + ['homeomorphism'])

        self.assertEqual(
            (expected_prev, expected_new),
            (sorted(self.prev_tree.get_fields()),
             sorted(self.new_tree.get_fields())))

    def test_get_structured_fields(self):
        expected_prev = self.get_all_fields()
        new_group = {'group_transformations': [
            {'bijective': [
                {'continuous': ['homeomorphism']},
                'isomorphism',
                'automorphism',
            ]},
            'endomorphism',
        ]}
        expected_new = ['start', 'end', 'current_date',
                        'math_degree', new_group]
        self.assertCountEqual(expected_prev, self.prev_tree.get_structured_fields())
        self.assertCountEqual(expected_new, self.new_tree.get_structured_fields())

