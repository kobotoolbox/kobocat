# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models.aggregates import Count
from django.utils import timezone

from onadata.apps.logger.models.instance import Instance
from onadata.apps.logger.models.attachment import Attachment
from onadata.apps.viewer.models.parsed_instance import ParsedInstance
from onadata.libs.utils.common_tags import MONGO_STRFTIME


class Command(BaseCommand):

    help = "Deletes revisions (by chunks) for a given app [and model]"

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)

        parser.add_argument(
            "--user",
            default=None,
            help="Specify a username to clean up only there forms",
        )

        parser.add_argument(
            "--xform",
            default=None,
            help="Specify a XForm's `id_string to clean up only this form",
        )

        parser.add_argument(
            "--delete",
            action='store_true',
            default=False,
            help="Force delete instead of soft delete (i.e tagging instance as deleted). Default is False",
        )

    def handle(self, *app_labels, **options):
        username = options['user']
        xform_id_string = options['xform']
        delete = options['delete']

        # Delete revisions.
        query = Instance.objects
        if xform_id_string:
            query = query.filter(xform__id_string=xform_id_string)

        if username:
            query = query.filter(xform__user__username=username)

        query = query.values_list(
            'uuid', flat=True
        ).annotate(
            count_uuid=Count('uuid')
        ).filter(
            count_uuid__gt=1
        ).distinct()

        for uuid in query.all():
            instances_with_same_uuid = Instance.objects.filter(uuid=uuid).\
                values_list('id', 'xml_hash').order_by('date_created')
            xml_hash_ref = None
            instance_id_ref = None

            duplicated_instances_ids = []
            for idx, instance_with_same_uuid in enumerate(instances_with_same_uuid):
                instance_id = instance_with_same_uuid[0]
                instance_xml_hash = instance_with_same_uuid[1]
                if idx == 0:
                    xml_hash_ref = instance_xml_hash
                    instance_id_ref = instance_id
                    continue

                if instance_xml_hash == xml_hash_ref:
                    duplicated_instances_ids.append(instance_id)
                else:
                    self.stdout.write('Not a duplicate #{}'.format(instance_id))

            with transaction.atomic():
                self.stdout.write('Link attachments to instance #{}'.format(instance_id_ref))
                # Update attachments
                Attachment.objects.filter(instance_id__in=duplicated_instances_ids).\
                    update(instance_id=instance_id_ref)

                # Update Mongo
                main_instance = Instance.objects.get(id=instance_id_ref)
                main_instance.parsed_instance.save()

                if delete:
                    self.stdout.write('\tDeleting instances: {}'.format(
                        duplicated_instances_ids))
                    Instance.objects.filter(id__in=duplicated_instances_ids).delete()
                    ParsedInstance.objects.\
                        filter(instance_id__in=duplicated_instances_ids).delete()
                    settings.MONGO_DB.instances.remove(
                        {'_id': {'$in': duplicated_instances_ids}}
                    )
                else:
                    self.stdout.write('\tDeleting (soft) instances: {}'.format(
                        duplicated_instances_ids))
                    # We could loop through instances and use `Instance.set_deleted()`
                    # but it would be way slower.
                    Instance.objects.filter(id__in=duplicated_instances_ids).\
                        update(deleted_at=timezone.now())
                    settings.MONGO_DB.instances.update_many(
                        {'_id': {'$in': duplicated_instances_ids}},
                        {'$set': {'_deleted_at': timezone.now().strftime(MONGO_STRFTIME)}}
                    )
                # Update number of submissions
                self.stdout.write(
                    '\tUpdating number of submissions of XForm #{} ({})'.format(
                        main_instance.xform.id, main_instance.xform.id_string))
                main_instance.xform.submission_count(force_update=True)
                self.stdout.write('')
            break
        else:
            self.stdout.write('No duplicates found')
