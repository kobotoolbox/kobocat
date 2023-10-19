from __future__ import annotations

from django.core.management.base import BaseCommand

from onadata.apps.logger.models import (
    Attachment,
    Instance,
)
from onadata.apps.logger.signals import pre_delete_attachment
from onadata.libs.utils.logger_tools import get_soft_deleted_attachments
from onadata.apps.viewer.models.parsed_instance import datetime_from_str


class Command(BaseCommand):

    help = "Soft delete orphan attachments, i.e: Hide them in API responses"

    def add_arguments(self, parser):
        parser.add_argument(
            '--chunks',
            type=int,
            default=2000,
            help='Number of records to process per query'
        )

        parser.add_argument(
            '--start-id',
            type=int,
            default=0,
            help='Instance ID to start from'
        )

        parser.add_argument(
            '--start-date',
            type=str,
            default=None,
            help='Starting date to start from. Format: yyyy-mm-aa.'
        )

    def handle(self, *args, **kwargs):
        chunks = kwargs['chunks']
        verbosity = kwargs['verbosity']
        start_id = kwargs['start_id']
        start_date = kwargs['start_date']

        queryset = Attachment.objects.values_list('instance_id', flat=True).distinct()

        if start_id:
            queryset = queryset.filter(instance_id__gte=start_id)

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

            if start_date and instance.date_created < datetime_from_str(
                f'{start_date}T00:00:00 +0000'
            ):
                if verbosity > 1:
                    message = '' if verbosity <= 1 else f' - {cpt}/{instances_count}'
                    self.stdout.write(
                        f'\tSkip Instance object #{instance_id}{message}. Too old'
                    )
                cpt += 1
                continue

            if not self._has_instance_been_edited(instance):
                if verbosity > 1:
                    message = '' if verbosity <= 1 else f' - {cpt}/{instances_count}'
                    self.stdout.write(
                        f'\tSkip Instance object #{instance_id}{message}. Not edited'
                    )
                cpt += 1
                continue

            try:
                soft_deleted_attachments = get_soft_deleted_attachments(instance)
            except Exception as e:
                cpt += 1
                if verbosity > 0:
                    self.stderr.write(
                        f'\tError for Instance object #{instance_id}: {str(e)}'
                    )
                continue

            for soft_deleted_attachment in soft_deleted_attachments:
                pre_delete_attachment(
                    soft_deleted_attachment, only_update_counters=True
                )
            if verbosity > 1:
                message = '' if verbosity <= 1 else f' - {cpt}/{instances_count}'
                self.stdout.write(
                    f'\tInstance object #{instance_id}{message} updated!'
                )
            cpt += 1

            cpt += 1
        self.stdout.write('Done!')

    def _has_instance_been_edited(self, instance):
        """
        Consider instance as edited if it modification date is more or less 10
        seconds apart
        """
        date_created_ts = instance.date_created.timestamp()
        date_modified_ts = instance.date_modified.timestamp()
        return not (
            date_created_ts <= date_modified_ts <= date_created_ts + 10
        )
