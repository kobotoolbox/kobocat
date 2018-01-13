from django.test import TestCase

from onadata.apps.logger.models.version import (
    VersionTree, VersionTreeException, last_common_item
)


class VersionTreeTestCase(TestCase):
    def setUp(self):
        self.root = VersionTree.objects.create()

    def _create_vt(self, parent):
        return VersionTree.objects.create(parent=parent)

    def test_get_root_path__already_root(self):
        self.assertEqual(VersionTree.objects.get_root_path(self.root), [self.root])

    def test_get_root_path(self):
        vt2 = self._create_vt(parent=self.root)
        vt3 = self._create_vt(parent=vt2)
        vt4 = self._create_vt(parent=vt3)
        self.assertEqual(VersionTree.objects.get_root_path(vt4), [self.root, vt2, vt3, vt4])

    def test_finding_path__same_node(self):
        self.assertEqual(VersionTree.objects.find_path(self.root, self.root), ([self.root], []))

    def test_finding_path__parent(self):
        vt2 = self._create_vt(parent=self.root)
        self.assertEqual(VersionTree.objects.find_path(vt2, self.root), ([vt2, self.root], []))

    def test_finding_path__grandparent(self):
        vt2 = self._create_vt(parent=self.root)
        vt3 = self._create_vt(parent=vt2)
        self.assertEqual(VersionTree.objects.find_path(vt3, self.root), ([vt3, vt2, self.root], []))

    def test_finding_path__other_branch(self):
        vt1 = self._create_vt(parent=self.root)
        vt2 = self._create_vt(parent=vt1)
        vt3 = self._create_vt(parent=vt1)
        vt4 = self._create_vt(parent=vt3)
        self.assertEqual(VersionTree.objects.find_path(vt2, vt4), ([vt2, vt1], [vt3, vt4]))

    def test_find_path_raises_exception_if_different_trees(self):
        vt_11 = self._create_vt(parent=self.root)
        vt_21 = self._create_vt(parent=None)
        vt_22 = self._create_vt(parent=vt_21)
        with self.assertRaises(VersionTreeException):
            VersionTree.objects.find_path(vt_11, vt_22)

    def test_last_common_item(self):
        xs, ys = [1, 2, 3, 4, 42], [1, 2, 3, 4, 17, 20]
        self.assertEqual(last_common_item(xs, ys), 3)

    def test_last_common_item_one_item(self):
        xs, ys = [1], [1]
        self.assertEqual(last_common_item(xs, ys), 0)

    def test_last_common_item__empty_list(self):
        xs, ys = [1, 2, 3], []
        self.assertEqual(last_common_item(xs, ys), -1)

    def test_last_common_item__no_common(self):
        xs, ys = [1, 2, 3, 4, 42], [5, 6, 7]
        self.assertEqual(last_common_item(xs, ys), -1)
