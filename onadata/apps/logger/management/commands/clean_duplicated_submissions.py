# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Sum
from django.db.models.aggregates import Count
from django.utils import timezone

from onadata.apps.logger.models.attachment import Attachment
from onadata.apps.logger.models.instance import Instance
from onadata.apps.viewer.models.parsed_instance import ParsedInstance
from onadata.apps.logger.models.xform import XForm
from onadata.libs.utils.common_tags import MONGO_STRFTIME


class Command(BaseCommand):

    help = "Deletes duplicated submissions (i.e same `uuid` and same `xml`)"

    def __init__(self, **kwargs):
        super(Command, self).__init__(**kwargs)
        self.__vaccuum = False
        self.__users = set([])

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)

        parser.add_argument(
            "--user",
            default=None,
            help="Specify a username to clean up only their forms",
        )

        parser.add_argument(
            "--xform",
            default=None,
            help="Specify a XForm's `id_string` to clean up only this form",
        )

        parser.add_argument(
            "--purge",
            action='store_true',
            default=False,
            help="Erase duplicate `Instance`s from the database entirely instead "
                 "of marking them as deleted using the `deleted_at` attribute. "
                 "Default is False",
        )

    def handle(self, *args, **options):
        username = options['user']
        xform_id_string = options['xform']
        purge = options['purge']

        # Retrieve all instances with the same `uuid`.
        query = Instance.objects
        if xform_id_string:
            query = query.filter(xform__id_string=xform_id_string)

        if username:
            query = query.filter(xform__user__username=username)

        # if we don't purge, we don't want to see instances
        # that have been marked as deleted. However, if we do purge
        # we do need these instances to be in the list in order
        # to delete them permanently
        if not purge:
            query = query.filter(deleted_at=None)

        query = query.values_list('uuid', flat=True)\
            .annotate(count_uuid=Count('uuid'))\
            .filter(count_uuid__gt=1)\
            .distinct()

        for uuid in query.all():

            duplicated_query = Instance.objects.filter(uuid=uuid)

            # if we don't purge, we don't want to see instances
            # that have been marked as deleted. However, if we do purge
            # we do need these instances to be in the list in order
            # to delete them permanently
            if not purge:
                duplicated_query = duplicated_query.filter(deleted_at=None)

            instances_with_same_uuid = duplicated_query.values_list('id',
                                                                    'xml_hash')\
                .order_by('xml_hash', 'date_created')
            xml_hash_ref = None
            instance_id_ref = None

            duplicated_instances_ids = []
            for instance_with_same_uuid in instances_with_same_uuid:
                instance_id = instance_with_same_uuid[0]
                instance_xml_hash = instance_with_same_uuid[1]

                if instance_xml_hash != xml_hash_ref:
                    self.__clean_up(instance_id_ref,
                                    duplicated_instances_ids,
                                    purge)
                    xml_hash_ref = instance_xml_hash
                    instance_id_ref = instance_id
                    duplicated_instances_ids = []
                    continue

                duplicated_instances_ids.append(instance_id)

            self.__clean_up(instance_id_ref,
                            duplicated_instances_ids,
                            purge)

        if not self.__vaccuum:
            if purge:
                self.stdout.write('No instances have been purged.')
            else:
                self.stdout.write('No instances have been marked as deleted.')
        else:
            # Update number of submissions for each user.
            for user_ in list(self.__users):
                result = XForm.objects.filter(user_id=user_.id)\
                    .aggregate(count=Sum('num_of_submissions'))
                user_.profile.num_of_submissions = result['count']
                self.stdout.write(
                    "\tUpdating `{}`'s number of submissions".format(
                        user_.username))
                user_.profile.save(update_fields=['num_of_submissions'])
                self.stdout.write(
                    '\t\tDone! New number: {}'.format(result['count']))

    def __clean_up(self, instance_id_ref, duplicated_instances_ids, purge):
        if instance_id_ref is not None and len(duplicated_instances_ids) > 0:
            self.__vaccuum = True
            with transaction.atomic():
                self.stdout.write('Link attachments to instance #{}'.format(
                    instance_id_ref))
                # Update attachments
                Attachment.objects.select_for_update()\
                    .filter(instance_id__in=duplicated_instances_ids)\
                    .update(instance_id=instance_id_ref)

                # Update Mongo
                main_instance = Instance.objects.select_for_update()\
                    .get(id=instance_id_ref)
                main_instance.parsed_instance.save()

                if purge:
                    self.stdout.write('\tPurging instances: {}'.format(
                        duplicated_instances_ids))
                    Instance.objects.select_for_update()\
                        .filter(id__in=duplicated_instances_ids).delete()
                    ParsedInstance.objects.select_for_update()\
                        .filter(instance_id__in=duplicated_instances_ids).delete()
                    settings.MONGO_DB.instances.remove(
                        {'_id': {'$in': duplicated_instances_ids}}
                    )
                else:
                    self.stdout.write('\tMarking instances as deleted: {}'.format(
                        duplicated_instances_ids))
                    # We could loop through instances and use `Instance.set_deleted()`
                    # but it would be way slower.
                    Instance.objects.select_for_update()\
                        .filter(id__in=duplicated_instances_ids)\
                        .update(deleted_at=timezone.now())
                    settings.MONGO_DB.instances.update_many(
                        {'_id': {'$in': duplicated_instances_ids}},
                        {'$set': {
                            '_deleted_at': timezone.now().strftime(MONGO_STRFTIME)
                        }}
                    )
                # Update number of submissions
                xform = main_instance.xform
                self.stdout.write(
                    '\tUpdating number of submissions of XForm #{} ({})'.format(
                        xform.id, xform.id_string))
                xform_submission_count = xform.submission_count(force_update=True)
                self.stdout.write(
                    '\t\tDone! New number: {}'.format(xform_submission_count))
                self.stdout.write('')

                self.__users.add(xform.user)
