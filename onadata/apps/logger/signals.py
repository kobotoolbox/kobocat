# coding: utf-8
import logging

from django.db.models import F
from django.db.models.signals import (
    pre_delete,
    post_save,
)
from django.dispatch import receiver

from onadata.apps.logger.models.attachment import Attachment
from onadata.apps.logger.models.xform import XForm
from onadata.apps.main.models.user_profile import UserProfile


@receiver(pre_delete, sender=Attachment)
def delete_attachment_subtract_user_profile_storage_bytes(instance, **kwargs):
    """
    Update the attachment_storage_bytes field in the UserProfile model
    when an attachment is deleted
    """
    attachment = instance
    file_size = attachment.media_file_size
    queryset = UserProfile.objects.filter(
        user_id=attachment.instance.xform.user_id
    )
    queryset.update(
        attachment_storage_bytes=F('attachment_storage_bytes') - file_size
    )


@receiver(pre_delete, sender=Attachment)
def delete_attachment_subtract_xform_storage_bytes(instance, **kwargs):
    """
    Update the attachment_storage_bytes field in the XForm
    model when an attachment is deleted
    """
    attachment = instance
    file_size = attachment.media_file_size
    xform_id = instance.instance.xform.pk
    queryset = XForm.objects.filter(pk=xform_id)
    queryset.update(
        attachment_storage_bytes=F('attachment_storage_bytes') - file_size
    )


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


@receiver(post_save, sender=Attachment)
def update_user_profile_attachment_storage_bytes(instance, created, **kwargs):
    """
    Update the attachment_storage_bytes field in the UserProfile model
    when an attachment is added
    """
    if not created:
        return
    attachment = instance
    if getattr(attachment, 'defer_counting', False):
        return
    file_size = attachment.media_file_size
    queryset = UserProfile.objects.filter(user_id=attachment.instance.xform.user_id)
    queryset.update(
        attachment_storage_bytes=F('attachment_storage_bytes') + file_size
    )


@receiver(post_save, sender=Attachment)
def update_xform_attachment_storage_bytes(instance, created, **kwargs):
    """
    Update the attachment_storage_bytes field in the XForm model when
    an attachment is added
    """
    if not created:
        return
    attachment = instance
    if getattr(attachment, 'defer_counting', False):
        return
    file_size = attachment.media_file_size
    xform_id = attachment.instance.xform_id
    queryset = XForm.objects.filter(pk=xform_id)
    queryset.update(
        attachment_storage_bytes=F('attachment_storage_bytes') + file_size
    )
