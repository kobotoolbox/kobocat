from django.db.models.signals import post_save, pre_save, post_delete

from onadata.apps.logger.models.instance import Instance, XForm


def update_xform_gsheets(sender, instance, created, **kwargs):
    pass


def delete_xform_gsheets(sender, instance, **kwargs):
    pass


def update_instance_gsheets(sender, instance, created, **kwargs):
    pass


def delete_instance_gsheets(sender, instance, **kwargs):
    pass


post_save.connect(update_xform_gsheets, sender=XForm,
                  dispatch_uid='update_xform_gsheets')
post_delete.connect(delete_xform_gsheets, sender=XForm,
                    dispatch_uid='delete_xform_gsheets')

post_save.connect(update_instance_gsheets, sender=Instance,
                  dispatch_uid='update_instance_gsheets')
post_delete.connect(delete_instance_gsheets, sender=Instance,
                    dispatch_uid='delete_instance_gsheets')