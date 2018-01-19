from django.test import TestCase

from onadata.apps.logger.data_migration.tree import Tree


class TestTree(TestCase):
    def setUp(self):
        super(TestTree, self).setUp()
        self.structure = ['a', 'b', {
            'c': ['c1', 'c2', {'c3': ['c31', 'c32']}]
        }, 'd']
        self.tree = Tree.construct_tree(self.structure)
        self.c_node = self.tree.find_child_by_label('c')
        self.c3_node = self.c_node.find_child_by_label('c3')
        self.c31_node = self.c3_node.find_child_by_label('c31')

    def test_construct_tree__basic(self):
        children = ['a', 'b', 'c']
        tree = Tree.construct_tree(children)
        self.assertEqual({
            'root_name': tree.label,
            'children': tree.get_child_attribs('label'),
            'children_parents': tree.get_child_attribs('parent'),
            'children_leafs': tree.get_child_attribs('is_leaf'),
        }, {
            'root_name': 'root',
            'children': children,
            'children_parents': [tree] * len(children),
            'children_leafs': [True, True, True],
        })

    def test_construct_tree__nested(self):
        self.assertEqual({
            'children_labels': self.tree.get_child_attribs('label'),
            'c_children': self.c_node.get_child_attribs('label'),
            'c3_children': self.c3_node.get_child_attribs('label'),
        }, {
            'children_labels': ['a', 'b', 'c', 'd'],
            'c_children': ['c1', 'c2', 'c3'],
            'c3_children': ['c1', 'c2', 'c3'],
        })

    def test_extract_ancestors_labels(self):
        self.assertEqual({
            'c31_parents': self.c3_node.extract_ancestors_labels(),
            'a_parents': self.tree\
                .find_child_by_label('a')\
                .extract_ancestors_labels()
        }, {
            'c31_parents': ['c3', 'c', 'root'],
            'a_parents': ['root'],
        })

