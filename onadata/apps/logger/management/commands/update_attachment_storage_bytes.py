#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 fileencoding=utf-8
# coding: utf-8
from collections import defaultdict

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import F, Sum

from onadata.apps.logger.models.attachment import Attachment
from onadata.apps.logger.models.xform import XForm
from onadata.apps.main.models.user_profile import UserProfile


class Command(BaseCommand):
    help = ('Retroactively add the total of '
            'the storage file per xform and user profile')

    def add_arguments(self, parser):
        parser.add_argument(
            '--max',
            '-m',
            type=int,
            help='PK of latest attachment included in the total',
            required=True,
        )

    def handle(self, *args, **kwargs):
        max_pk = kwargs['max']
        verbosity = kwargs['verbosity']

        # get the max attachments and xforms
        attachments = Attachment.objects.filter(pk__lte=max_pk)
        xforms = XForm.objects.all().values('pk', 'user_id', 'attachment_storage_bytes')
        max_per_user = defaultdict(int)

        # ensure the database roles back on failure
        with transaction.atomic():
            for xform in xforms:
                # write out xform progress
                if verbosity >= 1:
                    self.stdout.write(
                        f"Calculating attachments for xform_id #{xform['pk']}"
                    )
                # aggregate total media file size for all media per xform
                form_attachments = attachments.filter(
                    instance__xform_id=xform['pk']
                ).aggregate(total=Sum('media_file_size'))

                # check if total exists
                if form_attachments['total']:
                    XForm.objects.filter(pk=xform['pk']).update(
                        attachment_storage_bytes=F(
                            'attachment_storage_bytes'
                        ) + form_attachments['total']
                    )
                    max_per_user[xform['user_id']] += form_attachments['total']

            # add xform amount to User Profile
            for user_id, total_per_user in max_per_user.items():
                # write out user_id progress
                if verbosity >= 1:
                    self.stdout.write(
                        f'Adding xform total to user {user_id}'
                    )
                UserProfile.objects.filter(pk=user_id).update(
                    attachment_storage_bytes=F('attachment_storage_bytes')
                    + total_per_user
                )

        self.stdout.write('Done!')
