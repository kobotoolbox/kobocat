import json

from django.db import models
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.models import User

from onadata.apps.logger.models.xform import XForm, upload_to


class BackupManager(models.Manager):
    def form_backups(self, xform_id):
        return self.filter(xform_id=xform_id) \
                   .exclude() \
                   .order_by('-backup_version')

    def latest_backup(self, xform_id):
        return self.form_backups(xform_id).first()

    def latest_backup_with_changes(self, xform_id):
        return self.form_backups(xform_id) \
                   .exclude(migration_changes=u'') \
                   .first()


class BackupXForm(models.Model):
    xform_id = models.PositiveIntegerField()
    xls = models.FileField(upload_to=upload_to, null=True,
                           storage=FileSystemStorage())
    xml = models.TextField()
    description = models.TextField(default=u'', null=True)
    id_string = models.CharField(max_length=XForm.MAX_ID_LENGTH)

    _migration_changes = models.TextField(default=u'')

    user = models.ForeignKey(User, related_name='backup_xforms', null=True)
    date_created = models.DateTimeField()
    backup_version = models.DateTimeField(auto_now_add=True)

    objects = BackupManager()

    class Meta:
        app_label = 'data_migration'
        unique_together = ('xform_id', 'backup_version')

    @property
    def migration_changes(self):
        return json_loads_byteified(self._migration_changes)

    @migration_changes.setter
    def migration_changes(self, changes):
        self._migration_changes = json.dumps(changes)

    def __str__(self):
        return "{version} backup of xform {xform_id}".format(
            xform_id=self.xform_id,
            version=self.backup_version)


class BackupInstance(models.Model):
    xml = models.TextField()
    xform = models.ForeignKey(BackupXForm, null=True, related_name='surveys')
    date_created = models.DateTimeField()
    user = models.ForeignKey(User, related_name='backup_surveys', null=True)
    uuid = models.CharField(max_length=249, default=u'')

    class Meta:
        app_label = 'data_migration'

    def __str__(self):
        return "{version} backup of instance {uuid}".format(
            uuid=self.uuid,
            version=self.xform.backup_version)


def json_loads_byteified(json_text):
    """
    Json loads returning byte strings instead of unicode
    Based on: https://stackoverflow.com/a/33571117/5056023
    """
    return _byteify(json.loads(json_text, object_hook=_byteify), ignore_dicts=True)


def _byteify(data, ignore_dicts=False):
    if isinstance(data, unicode):
        return data.encode('utf-8')
    if isinstance(data, list):
        return [_byteify(item, ignore_dicts=True) for item in data]
    # if this is a dictionary, return dictionary of byteified keys and values
    # but only if we haven't already byteified it
    if isinstance(data, dict) and not ignore_dicts:
        return {
            _byteify(key, ignore_dicts=True): _byteify(value, ignore_dicts=True)
            for key, value in data.iteritems()
        }
    return data
