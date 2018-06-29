from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from onadata.apps.data_migration.xformtree import XFormTree
from onadata.apps.logger.models import XForm


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
        app_label = 'data_migration'

    def __str__(self):
        if self.version:
            return "VersionTree: form={}, version={}".format(
                self.version.xform_id,
                self.version.backup_version,
            )
        return "VersionTree {}".format(self.id)


class XFormVersion(models.Model):
    xform = models.OneToOneField(XForm, on_delete=models.CASCADE)
    version_tree = models.ForeignKey(VersionTree, blank=True, null=True)

    class Meta:
        app_label = 'data_migration'

    @property
    def latest_backup(self):
        return self.version_tree.version


@receiver(post_save, sender=XForm)
def create_xform_version(instance, created, **kwargs):
    if created:
        XFormVersion.objects.create(xform=instance)


def change_id_string(xform, new_id_string):
    xform.id_string = new_id_string
    xformtree = XFormTree(xform.xml)
    xformtree.set_id_string(new_id_string)
    xform.xml = xformtree.to_xml()
    return xform


def create_xform_copy(xform, id_string_suffix='temp'):
    """Create copy of xform.
    https://docs.djangoproject.com/en/dev/topics/db/queries/#copying-model-instances
    """
    temp_xform = xform
    temp_xform.pk = None
    new_id_string = '%s-%s' % (temp_xform.id_string, id_string_suffix)
    change_id_string(temp_xform, new_id_string)
    temp_xform.sms_id_string += '-' + id_string_suffix

    temp_xform.save()
    return temp_xform


def copy_xform_data(from_xform, to_xform):
    """
    Copy only fields that can be changed by user during new xls file upload
    """
    to_xform.xls = from_xform.xls
    to_xform.xml = from_xform.xml
    to_xform.json = from_xform.json
    change_id_string(to_xform, to_xform.id_string)
    to_xform.description = from_xform.description
    to_xform.date_created = from_xform.date_created
    to_xform.save()
