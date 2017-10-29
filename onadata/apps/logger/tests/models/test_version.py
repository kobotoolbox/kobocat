from django.test import TestCase

from onadata.apps.logger.models import VersionTree


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
        self.assertEqual(VersionTree.objects.get_root_path(vt4), [vt4, vt3, vt2, self.root])

    def test_finding_path__same_node(self):
        self.assertEqual(VersionTree.objects.find_path(self.root, self.root), ([], []))

    def test_finding_path__parent(self):
        vt2 = self._create_vt(parent=self.root)
        self.assertEqual(VersionTree.objects.find_path(vt2, self.root), ([vt2], []))

    def test_finding_path__grandparent(self):
        vt2 = self._create_vt(parent=self.root)
        vt3 = self._create_vt(parent=vt2)
        self.assertEqual(VersionTree.objects.find_path(vt3, self.root), ([vt3, vt2], []))

    def test_finding_path__other_branch(self):
        vt1 = self._create_vt(parent=self.root)
        vt2 = self._create_vt(parent=vt1)
        vt3 = self._create_vt(parent=vt1)
        vt4 = self._create_vt(parent=vt3)
        self.assertEqual(VersionTree.objects.find_path(vt2, vt4), ([vt2], [vt3, vt4]))
