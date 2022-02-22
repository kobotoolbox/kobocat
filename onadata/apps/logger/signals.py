# coding: utf-8
import logging
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from onadata.apps.logger.models.attachment import Attachment


@receiver(pre_delete, sender=Attachment)
def post_delete_asset(instance, **kwargs):
    # Unfortunately, it seems that Django does not call Model.delete() on
    # delete CASCADE. But this signal is called though.
    # We want to delete all files when an Instance (or Attachment) object is
    # deleted.
    try:
        instance.media_file.delete()
    except Exception as e:
        logger = logging.getLogger('console_logger')
        logger.error(str(e), exc_info=True)
