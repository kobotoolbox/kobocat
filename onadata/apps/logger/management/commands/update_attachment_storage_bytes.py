#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 fileencoding=utf-8
# coding: utf-8
import json
from collections import defaultdict
from typing import Dict

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Sum

from onadata.apps.logger.models.attachment import Attachment
from onadata.apps.logger.models.instance import Instance
from onadata.apps.logger.models.xform import XForm
from onadata.apps.main.models.user_profile import UserProfile
from onadata.libs.utils.jsonbfield_helper import ReplaceValues


class Command(BaseCommand):
    help = (
        'Retroactively add the total of '
        'the storage file per xform and user profile'
    )

    def handle(self, *args, **kwargs):
        self.verbosity = kwargs['verbosity']

        # Dictionary which contains the total of bytes for each user. Useful
        # to avoid another aggregate query on attachments to calculate users
        # global usage.
        total_per_user = defaultdict(int)

        # Release any locks on the users' profile from getting submissions
        UserProfile.objects.exclude(
            metadata__attachments_counting_status='complete'
        ).update(
            metadata=ReplaceValues(
                'metadata',
                updates={'submissions_suspended': False},
            ),
        )

        # Get only xforms whose users' storage counters have not been updated yet.
        up_queryset = UserProfile.objects.values_list('user_id', flat=True).filter(
            metadata__attachments_counting_status='complete'
        )
        xforms = (
            XForm.objects.exclude(user_id__in=up_queryset)
            .values('pk', 'user_id', 'user__username')
            .order_by('user_id')
        )

        last_xform = None
        for xform in xforms:

            if not last_xform or (last_xform['user_id'] != xform['user_id']):
                # Retrieve or create user's profile.
                (
                    user_profile,
                    created,
                ) = UserProfile.objects.get_or_create(user_id=xform['user_id'])

                # Set the flag to true if it was never set.
                if not user_profile.metadata.get('submissions_suspended'):
                    # We are using the flag `submissions_suspended` to prevent
                    # new submissions from coming in while the
                    # `attachment_storage_bytes` is being calculated.
                    user_profile.metadata['submissions_suspended'] = True
                    user_profile.save(update_fields=['metadata'])

                # if `last_xform` is not none, it means that the `user_id` is
                # different from the previous one in the loop so the user
                # profile must be updated
                if last_xform:
                    self.update_user_profile(
                        last_xform, total_per_user[last_xform['user_id']]
                    )

            # write out xform progress
            if self.verbosity >= 1:
                self.stdout.write(
                    f"Calculating attachments for xform_id #{xform['pk']}"
                    f" (user {xform['user__username']})"
                )
            # aggregate total media file size for all media per xform
            # We cannot get the sum of all attachments for on xform because
            # we need to make two joins with Instance and XForm models.
            # It is really slow on big databases. So, to avoid that, we make
            # another extra query to get all the instance ids to pass it to
            # Attachment queryset.
            instance_ids = Instance.objects.values_list('pk', flat=True).filter(
                xform_id=xform['pk']
            )

            # It does not seem to have a real limit of number of parameters in
            # "IN" clause in PostgreSQL but for safety, we use chunks to pass
            # to `instance_id__in` just in case a form has a huge numbers
            # of submissions.
            # See https://stackoverflow.com/questions/1009706/postgresql-max-number-of-parameters-in-in-clause
            instance_ids_count = len(instance_ids)
            max_ids_per_query = 5000
            chunks = [
                instance_ids[x:x + max_ids_per_query]
                for x in range(0, instance_ids_count, max_ids_per_query)
            ]
            form_attachments_total = 0
            for idx, chunk in enumerate(chunks):
                if self.verbosity > 1:
                    self.stdout.write(
                        f'\tCalculating total: {idx+1}/{len(chunks)} instance ID'
                        f' chunks'
                    )
                form_attachments = Attachment.objects.filter(
                    instance_id__in=chunk
                ).aggregate(total=Sum('media_file_size'))
                if form_attachments['total']:
                    form_attachments_total += form_attachments['total']

            if form_attachments_total:
                with transaction.atomic():
                    if self.verbosity >= 1:
                        self.stdout.write(
                            f'\tUpdating xform attachment storage to '
                            f"{form_attachments_total} bytes"
                        )

                    XForm.objects.select_for_update().filter(
                        pk=xform['pk']
                    ).update(
                        attachment_storage_bytes=form_attachments_total
                    )

                total_per_user[xform['user_id']] += form_attachments_total
            elif self.verbosity >= 1:
                self.stdout.write('\tNo attachments found')

            last_xform = xform

        # need to call `update_user_profile()` one more time outside the loop
        # because the last user profile will not be up-to-date otherwise
        if last_xform:
            self.update_user_profile(
                last_xform, total_per_user[last_xform['user_id']]
            )

        if self.verbosity >= 1:
            self.stdout.write('Done!')

    def update_user_profile(self, xform: Dict, total: int):
        user_id = xform['user_id']
        username = xform['user__username']

        if self.verbosity >= 1:
            self.stdout.write(
                f'Updating attachment storage total ({total} bytes) on '
                f'{username}’s profile'
            )

        # Update user's profile (and lock the related row)
        with transaction.atomic():
            updates = {
                'submissions_suspended': False,
                'attachments_counting_status': 'complete',
            }
            UserProfile.objects.select_for_update().filter(
                user_id=user_id
            ).update(
                attachment_storage_bytes=total,
                metadata=ReplaceValues(
                    'metadata',
                    updates=updates,
                ),
            )
