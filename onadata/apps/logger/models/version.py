from django.db import models


class VersionTreeException(Exception):
    pass


class VersionManager(models.Manager):
    @staticmethod
    def get_root_path(vt):
        """Get path from root to given vt"""
        path = []
        while vt is not None:
            path.append(vt)
            vt = vt.parent
        return list(reversed(path))

    def find_path(self, vt1, vt2):
        """Find and return path from vt1 to vt2
        :rtype: tuple of two lists ([path up], [path down])
        """
        vt1_root_path = self.get_root_path(vt1)
        vt2_root_path = self.get_root_path(vt2)

        if vt1_root_path[0] != vt2_root_path[0]:
            raise VersionTreeException(
                'Path not found. Passed nodes (vt1 = %s, vt2 = %s) '
                'are from different version trees' % (str(vt1), str(vt2))
            )
        last_common_node = last_common_item(vt1_root_path, vt2_root_path)
        return (vt1_root_path[last_common_node:][::-1],
                vt2_root_path[last_common_node + 1:])


def last_common_item(xs, ys):
    """Search for index of last common item in two lists."""
    max_i = min(len(xs), len(ys)) - 1
    for i, (x, y) in enumerate(zip(xs, ys)):
        if x == y and (i == max_i or xs[i+1] != ys[i+1]):
            return i
    return -1


class VersionTree(models.Model):
    parent = models.ForeignKey('self', related_name='nodes',
                               blank=True, null=True)
    version = models.OneToOneField('BackupXForm', related_name='version_tree',
                                   blank=True, null=True)

    objects = VersionManager()

    class Meta:
        app_label = 'logger'

    def __str__(self):
        if self.version:
            return "VersionTree: form={}, version={}".format(
                self.version.xform_id,
                self.version.backup_version,
            )
        return "VersionTree {}".format(self.id)
