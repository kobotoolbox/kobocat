from lxml import etree

from onadata.apps.data_migration.surveytree import (
    SurveyTree, MissingFieldException
)
from .common import CommonTestCase
from onadata.apps.data_migration.tests import fixtures


class SurveyTreeOperationsTest(CommonTestCase):
    def setUp(self):
        super(SurveyTreeOperationsTest, self).setUp()
        self.survey = SurveyTree(fixtures.survey_xml)

    def test_get_fields(self):
        self.assertTrue(all(map(etree.iselement, self.survey.get_fields())))
        self.assertEqual(
            self.survey.get_fields_names(),
            fixtures.FIELDS
        )

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
        field = self.survey.get_field('name')
        self.survey.permanently_remove_field(field)
        self.assertEqual(self.survey.get_fields_names(), expected)

    def test_change_field_tag(self):
        expected = fixtures.FIELDS[:]
        pos = expected.index('name')
        expected[pos] = 'first_name'
        field = self.survey.get_field('name')
        self.survey.change_field_tag(field, 'first_name')
        self.assertEqual(self.survey.get_fields_names(), expected)

    def test_get_or_create_field(self):
        expected = fixtures.FIELDS[:]
        expected.append('opinion')
        self.survey.get_or_create_field('opinion')
        self.survey.get_or_create_field('name')
        self.assertEqual(self.survey.get_fields_names(), expected)

    def test_get_or_create_field__should_add_if_already_exist(self):
        self.survey.get_or_create_field('name')
        self.assertEqual(self.survey.get_fields_names(), fixtures.FIELDS[:])

    def test_get_or_create_field_with_groups(self):
        survey = SurveyTree('<AlgebraicTypes>'
                            '<functor></functor>'
                            '</AlgebraicTypes>')
        survey.get_or_create_field('functor')
        survey.get_or_create_field('applicative', groups=['functor'])
        survey.get_or_create_field('monad', groups=['applicative'], text='Either')
        self.assertXMLsEqual(survey.to_string(), '''
            <AlgebraicTypes>
                <functor> 
                    <applicative>
                        <monad>Either</monad>
                    </applicative>
                </functor>
            </AlgebraicTypes>
        ''')


class SurveyTreeWithGroupsOperationsTest(CommonTestCase):
    def setUp(self):
        super(SurveyTreeWithGroupsOperationsTest, self).setUp()
        self.survey_prev = SurveyTree(fixtures.survey_xml_groups_before__second)
        self.survey = SurveyTree(fixtures.survey_xml_groups_after__second)

    def test_find_group(self):
        self.assertTrue(etree.iselement(self.survey.find_group('bijective')))
        self.assertTrue(etree.iselement(self.survey.find_group(
            'group_transformations'
        )))

    def test_get_groups_names(self):
        self.assertEqual(sorted(self.survey.get_groups_names()),
                         ['bijective', 'continuous', 'group_transformations'])

    def test_find_group__raises_on_normal_field(self):
        with self.assertRaises(MissingFieldException):
            self.survey.find_group('isomorphism')

    def test_find_group__raises_on_no_such_group(self):
        with self.assertRaises(MissingFieldException):
            self.survey.find_group('certainly_no_such_group_exist')

    def test_get_all_elems(self):
        self.assertCountEqual(fixtures.GROUPS_FIELDS_AFTER,
                              [e.tag for e in self.survey.get_all_elems()])

    def test_insert_field_into_group_chain(self):
        survey = SurveyTree('<AlgebraicTypes></AlgebraicTypes>')
        monad = survey.create_element('monad', 'Either')
        foldable = survey.create_element('foldable')
        monoid = survey.create_element('monoid', 'assoc and id')
        survey.insert_field_into_group_chain(monad, ['functor', 'applicative'])
        survey.insert_field_into_group_chain(foldable, ['functor'])
        survey.insert_field_into_group_chain(monoid, ['semigroup'])
        self.assertXMLsEqual(survey.to_string(), '''
            <AlgebraicTypes>
                <functor> 
                    <applicative>
                        <monad>Either</monad>
                    </applicative>
                    <foldable/>
                </functor>
                <semigroup>
                    <monoid>assoc and id</monoid>
                </semigroup> 
            </AlgebraicTypes>
        ''')

    def test_insert_field_into_group_chain__real_world_scenario(self):
        fields_names = ['isomorphism', 'automorphism', 'endomorphism']
        new_field = self.survey_prev.create_element('homeomorphism')
        fields = [new_field] + list(map(self.survey_prev.get_field, fields_names))
        fields_groups = [['group_transformations', 'bijective', 'continuous'],
                         ['group_transformations', 'bijective'],
                         ['group_transformations', 'bijective'],
                         ['group_transformations']]

        for field, groups in zip(fields, fields_groups):
            self.survey_prev.insert_field_into_group_chain(field, groups)

        expected_xml = self.survey_prev.to_string()\
            .replace('TestGroup', 'AlgebraicTypes2')
        self.assertXMLsEqual(expected_xml, fixtures.survey_xml_groups_after__second)
