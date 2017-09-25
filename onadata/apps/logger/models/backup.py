from django.db import models
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.models import User

from .xform import upload_to


class BackupXForm(models.Model):
    xls = models.FileField(upload_to=upload_to, null=True,
                           storage=FileSystemStorage())
    xml = models.TextField()
    json = models.TextField(default=u'')
    description = models.TextField(default=u'', null=True)

    user = models.ForeignKey(User, related_name='backup_xforms', null=True)
    date_created = models.DateTimeField()
    backup_version = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'logger'


class BackupInstance(models.Model):
    xml = models.TextField()
    xform = models.ForeignKey(BackupXForm, null=True, related_name='surveys')
    date_created = models.DateTimeField()
    user = models.ForeignKey(User, related_name='backup_surveys', null=True)

    class Meta:
        app_label = 'logger'
