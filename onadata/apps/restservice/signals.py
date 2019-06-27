# -*- coding: utf-8 -*-
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from onadata.apps.restservice import SERVICE_KPI_HOOK
from onadata.apps.logger.models import XForm
from onadata.apps.restservice.models import RestService


@receiver(post_save, sender=XForm)
def save_kpi_hook_service(sender, instance, **kwargs):
    """
    Creates/Deletes Kpi hook Rest service related to XForm instance
    :param sender: XForm class
    :param instance: XForm instance
    :param kwargs: dict
    """
    kpi_hook_service = instance.kpi_hook_service
    if instance.has_kpi_hooks:
        # Only register the service if it hasn't been created yet.
        if kpi_hook_service is None:
            kpi_hook_service = RestService(
                service_url=settings.KPI_HOOK_ENDPOINT_PATTERN.format(
                    asset_uid=instance.id_string),
                xform=instance,
                name=SERVICE_KPI_HOOK[0]
            )
            kpi_hook_service.save()
    elif kpi_hook_service is not None:
        # Only delete the service if it already exists.
        kpi_hook_service.delete()
