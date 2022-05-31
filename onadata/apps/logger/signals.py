# coding: utf-8
import logging
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from onadata.apps.logger.models.attachment import Attachment


@receiver(pre_delete, sender=Attachment)
def pre_delete_attachment(instance, **kwargs):
    # "Model.delete() isn’t called on related models, but the pre_delete and
    # post_delete signals are sent for all deleted objects." See
    # https://docs.djangoproject.com/en/2.2/ref/models/fields/#django.db.models.CASCADE
    # We want to delete all files when an Instance (or Attachment) object is
    # deleted.

    # `instance` here means "model instance", and no, it is not allowed to
    # change the name of the parameter
    attachment = instance
    try:
        attachment.media_file.delete()
    except Exception as e:
        logging.error('Failed to delete attachment: ' + str(e), exc_info=True)
