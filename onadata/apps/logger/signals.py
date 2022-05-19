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
def delete_user_profile_attachment_storage_bytes(instance, **kwargs):
    """
    Update the attachment_storage_bytes field in the UserProfile model
    when an attachment is deleted
    """
    file_size = instance.media_file.size
    owner_profile = instance.instance.xform.user.profile.pk
    queryset = UserProfile.objects.filter(pk=owner_profile)
    queryset.update(
        attachment_storage_bytes=F('attachment_storage_bytes') - file_size
    )


@receiver(pre_delete, sender=Attachment)
def delete_xform_attachment_storage_bytes(instance, **kwargs):
    """
    Update the attachment_storage_bytes field in the XForm
    model when an attachment is deleted
    """
    file_size = instance.media_file.size
    xform = instance.instance.xform.pk
    queryset = XForm.objects.filter(pk=xform)
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
    # Probably not necessary right now, but in case needed in the future
    if getattr(instance, 'defer_counting', False):
        return
    file_size = instance.media_file.size
    user_profile = instance.instance.xform.user.profile.pk
    queryset = UserProfile.objects.filter(pk=user_profile)
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
    # Probably not needed now, but in case needed in the future
    if getattr(instance, 'defer_counting', False):
        return
    file_size = instance.media_file.size
    xform = instance.instance.xform.pk
    queryset = XForm.objects.filter(pk=xform)
    queryset.update(
        attachment_storage_bytes=F('attachment_storage_bytes') + file_size
    )
