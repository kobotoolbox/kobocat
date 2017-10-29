from django.db import models


class VersionTreeException(Exception):
    pass


class VersionManager(models.Manager):
    def get_root_path(self, vt):
        path = []
        while vt is not None:
            path.append(vt)
            vt = vt.parent
        return path

    def find_path(self, vt1, vt2):
        """Find and return path from vt1 to vt2
        :rtype: tuple of two lists ([path up], [path down])
        """
        vt1_root_path = self.get_root_path(vt1)
        vt2_root_path = self.get_root_path(vt2)

        for i, node in enumerate(vt1_root_path):
            if node in vt2_root_path:
                j = vt2_root_path.index(node)
                return (vt1_root_path[:i + 1], vt2_root_path[:j + 1][::-1])
        else:
            raise VersionTreeException(
                'Path not found. Passed nodes (vt1 = %s, vt2 = %s) '
                'are from different version trees' % (str(vt1), str(vt2))
            )


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
            return "VersionTree: form=%s, version=%s" % (
                self.version.xform_id,
                self.version.backup_version,
            )
        return "VersionTree %s" % self.id
