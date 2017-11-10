import os
import mimetypes

from hashlib import md5
from django.db import models

from instance import Instance


def upload_to(attachment, filename):
    instance = attachment.instance
    xform = instance.xform
    return os.path.join(
        xform.user.username,
        'attachments',
        xform.uuid or 'form',
        instance.uuid or 'instance',
        os.path.split(filename)[1])


class Attachment(models.Model):
    instance = models.ForeignKey(Instance, related_name="attachments")
    media_file = models.FileField(upload_to=upload_to, max_length=380, db_index=True)
    mimetype = models.CharField(
        max_length=100, null=False, blank=True, default='')

    class Meta:
        app_label = 'logger'

    def save(self, *args, **kwargs):
        if self.media_file and self.mimetype == '':
            # guess mimetype
            mimetype, encoding = mimetypes.guess_type(self.media_file.name)
            if mimetype:
                self.mimetype = mimetype
        super(Attachment, self).save(*args, **kwargs)

    @property
    def file_hash(self):
        if self.media_file.storage.exists(self.media_file.name):
            return u'%s' % md5(self.media_file.read()).hexdigest()
        return u''

    @property
    def filename(self):
        return os.path.basename(self.media_file.name)
