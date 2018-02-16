
class Tree(object):
    def __init__(self, label='root', parent=None, children=None):
        self.label = label
        self.parent = parent
        self.children = []

        for child in (children or []):
            self.add_child(child)

    def __repr__(self):
        return "Tree label: {}, children: {}".format(self.label, self.children)

    def add_child(self, node):
        assert isinstance(node, Tree)
        self.children.append(node)

    def find_child_by_label(self, label):
        results = [child for child in self.children if child.label == label]
        return next(iter(results), None)

    def get_child_attribs(self, attrib):
        rev_getattr = lambda obj: getattr(obj, attrib)
        return map(rev_getattr, self.children)

    @property
    def is_leaf(self):
        return self.children == []

    def search_node_by_label(self, label):
        return self._dfs_search_node(self, label)

    @classmethod
    def _dfs_search_node(cls, tree, label):
        for child in tree.children:
            if child.is_leaf and child.label == label:
                return child
            child_search = cls._dfs_search_node(child, label)
            if child_search:
                return child_search
        return None

    @staticmethod
    def extract_ancestors_labels(node):
        """Return a list of ancestors labels"""
        labels = []
        current_parent = node.parent
        while current_parent is not None:
            labels.append(current_parent.label)
            current_parent = current_parent.parent
        return labels

    @classmethod
    def construct_tree(cls, iterable, root=None):
        """Construct tree from plain python data structures
        iterable format: [
            'leaf1_label', 'leaf2_label', {
                'node1_label': ['node1_leaf_label', {
                    nested_node_label: [...]
                }]
            }
        ]

        :param iterable:
        :param Tree root: root of the iterable, by default creates one
        :rtype: Tree
        """
        root = root or Tree()
        cls._construct_children(root, iterable)
        return root

    @classmethod
    def _construct_children(cls, root, children):
        for child in children:
            node = cls._construct_child(root, child)
            root.add_child(node)

    @classmethod
    def _construct_child(cls, root, elem):
        if type(elem) == dict:
            node_label, node_children = next(elem.iteritems())
            return cls._construct_node_with_children(root, node_label,
                                                     node_children)
        return Tree(label=elem, parent=root)

    @classmethod
    def _construct_node_with_children(cls, root, root_label, children):
        node = Tree(label=root_label, parent=root)
        cls.construct_tree(children, node)
        return node
