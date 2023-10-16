from __future__ import annotations

from django.core.management.base import BaseCommand

from onadata.apps.logger.models import (
    Attachment,
    Instance,
)
from onadata.apps.logger.signals import pre_delete_attachment
from onadata.libs.utils.logger_tools import get_soft_deleted_attachments


class Command(BaseCommand):

    help = "Soft delete orphan attachments, i.e: Hide them in API responses"

    def add_arguments(self, parser):
        parser.add_argument(
            '--chunks',
            type=int,
            default=2000,
            help="Number of records to process per query"
        )

    def handle(self, *args, **kwargs):
        chunks = kwargs['chunks']
        verbosity = kwargs['verbosity']

        queryset = Attachment.objects.values_list('instance_id', flat=True).distinct()

        if verbosity > 1:
            self.stdout.write(
                f'Calculating number of instance with attachments…'
            )
            instances_count = queryset.count()

        cpt = 1

        for instance_id in queryset.iterator(chunk_size=chunks):
            instance = Instance.objects.get(pk=instance_id)
            if verbosity > 0:
                message = '' if verbosity <= 1 else f' - {cpt}/{instances_count}'
                self.stdout.write(
                    f'Processing Instance object #{instance_id}{message}…'
                )
            soft_deleted_attachments = get_soft_deleted_attachments(instance)
            for soft_deleted_attachment in soft_deleted_attachments:
                pre_delete_attachment(
                    soft_deleted_attachment, only_update_counters=True
                )

            cpt += 1
        self.stdout.write('Done!')
