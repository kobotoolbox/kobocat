from django.test import TestCase

from onadata.apps.logger.data_migration.compare_xml import XFormsComparator

from . import fixtures


class CompareXMLTestCase(TestCase):
    def setUp(self):
        self.RealComparator = XFormsComparator(fixtures.form_xml_case_1,
                                               fixtures.form_xml_case_1_after)
        # Used when no rational data is needed
        self.DummyComparator = XFormsComparator('<a></a>', '<b></b>')
        self.added_fields = ['first_name', 'last_name', 'birthday']
        self.removed_fields = ['name', 'date']

    def clean_tag(self, tag):
        return self.DummyComparator.clean_tag(tag)

    def test_clean_tag(self):
        header = '{http://www.w3.org/1999/xhtml}title'
        result = self.DummyComparator.clean_tag(header)
        self.assertEqual(result, 'title')

        result = self.DummyComparator.clean_tag('title')
        self.assertEqual(result, 'title')

    def test_titles_diff(self):
        self.assertEqual(self.RealComparator.titles_diff(), 'Survey2')

    def test_fields_diff(self):
        self.assertEqual(
            self.RealComparator.fields_diff(),
            (self.added_fields, self.removed_fields))

    def test_fields_type_diff(self):
        self.assertEqual(
            self.RealComparator.fields_type_diff(), {'age': 'decimal'}
        )

    def test_input_obligation_diff(self):
        self.assertEqual(
            self.RealComparator.input_obligation_diff(), {'location': False}
        )

    def test_pprint_dict(self):
        self.assertEqual(
            self.DummyComparator.pprint_dict(**{'abc': 123}),
            'Name: abc, new value: 123\n',
        )

    def test_sanity_check_comparison_results(self):
        self.assertEqual(
            self.RealComparator.titles_diff(),
            self.RealComparator.comparison_results()['new_title'],
        )

    def test_comparison_result(self):
        expected_result = {
            'new_title': 'Survey2',
            'fields_added': self.added_fields,
            'fields_removed': self.removed_fields,
            'input_obligation_diff': 'Name: location, new value: False\n',
            'fields_type_diff': 'Name: age, new value: decimal\n',
        }
        self.assertEqual(
            self.RealComparator.comparison_results(),
            expected_result,
        )

    def test_select_diff(self):
        self.assertEqual(
            self.RealComparator.selects_diff(),
            ({'gender': ['unknown']}, {}),
        )


class CompareXMLWithGroupsTestCase(TestCase):
    def setUp(self):
        self.comparator = XFormsComparator(
            fixtures.form_xml_groups_before__second,
            fixtures.form_xml_groups_after__second)

    def test_fields_groups(self):
        fields_groups = self.comparator.fields_groups_new()
        bijective_group = ['group_transformations', 'bijective']
        self.assertEqual(
            fields_groups, {
                'isomorphism': bijective_group,
                'automorphism': bijective_group,
                'homeomorphism': bijective_group + ['continuous'],
                'endomorphism': ['group_transformations'],
                'start': [],
                'end': [],
                'math_degree': [],
                'current_date': [],
            }
        )

