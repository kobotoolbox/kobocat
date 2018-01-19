
class Tree(object):
    def __init__(self, label='root', parent=None, children=None):
        self.label = label
        self.parent = parent
        self.children = []

        for child in (children or []):
            self.add_child(child)

    def __repr__(self):
        return self.label

    def add_child(self, node):
        assert isinstance(node, Tree)
        self.children.append(node)

    def find_child_by_label(self, label):
        return next(
            [child for child in self.children if child.label == label], None
        )

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

    def extract_ancestors_labels(self):
        labels = []
        current_parent = self.parent
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
        cls.construct_children(root, iterable)
        return root

    @classmethod
    def construct_children(cls, root, children):
        for child in children:
            cls._construct_child(root, child)

    @classmethod
    def _construct_child(cls, root, elem):
        node_label, node_children = elem.iteritems()[0]
        node = (cls._construct_node_with_children(root, node_label,
                                                  node_children)
                if type(elem) == dict
                else Tree(label=elem, parent=root))
        root.add_child(node)

    @classmethod
    def _construct_node_with_children(cls, root, root_label, children):
        node = Tree(label=root_label, parent=root)
        cls.construct_tree(children, node)
        return node
