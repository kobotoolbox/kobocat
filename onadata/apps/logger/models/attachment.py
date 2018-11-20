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

    MEDIA_FILE_BASENAME_PATTERN = re.compile(r'/([^/]+)$')

    class Meta:
        app_label = 'logger'

    def _populate_media_file_basename(self):
        # TODO: write a management command to call this (and save) for all
        # existing attachments?  For the moment, the `media_file_basename`
        # column can be populated directly in Postgres using:
        #   UPDATE logger_attachment
        #     SET media_file_basename = substring(media_file from '/([^/]+)$');
        if self.media_file:
            match = re.search(
                self.MEDIA_FILE_BASENAME_PATTERN, self.media_file.name)
            if match:
                self.media_file_basename = match.groups()[0]
            else:
                self.media_file_basename = ''

    def save(self, *args, **kwargs):
        if self.media_file and self.mimetype == '':
            # guess mimetype
            mimetype, encoding = mimetypes.guess_type(self.media_file.name)
            if mimetype:
                self.mimetype = mimetype

        self._populate_media_file_basename()

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
