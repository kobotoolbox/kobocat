import os
import re
import mimetypes

from hashlib import md5
from django.db import models

from instance import Instance


def generate_attachment_filename(instance, filename):
    xform = instance.xform
    return os.path.join(
        xform.user.username,
        'attachments',
        xform.uuid or 'form',
        instance.uuid or 'instance',
        os.path.split(filename)[1])


def upload_to(attachment, filename):
    return generate_attachment_filename(attachment.instance, filename)


def hash_attachment_contents(contents):
    return u'%s' % md5(contents).hexdigest()


class Attachment(models.Model):
    instance = models.ForeignKey(Instance, related_name="attachments")
    media_file = models.FileField(upload_to=upload_to, max_length=380, db_index=True)
    media_file_basename = models.CharField(
        max_length=260, null=True, blank=True, db_index=True)
    mimetype = models.CharField(
        max_length=100, null=False, blank=True, default='')

    class Meta:
        app_label = 'logger'

    def save(self, *args, **kwargs):
        if self.media_file:
            self.media_file_basename = self.filename
            if self.mimetype == '':
                # guess mimetype
                mimetype, encoding = mimetypes.guess_type(self.media_file.name)
                if mimetype:
                    self.mimetype = mimetype

        super(Attachment, self).save(*args, **kwargs)

    @property
    def file_hash(self):
        if self.media_file.storage.exists(self.media_file.name):
            media_file_position = self.media_file.tell()
            self.media_file.seek(0)
            media_file_hash = hash_attachment_contents(self.media_file.read())
            self.media_file.seek(media_file_position)
            return media_file_hash
        return u''

    @property
    def filename(self):
        return os.path.basename(self.media_file.name)
