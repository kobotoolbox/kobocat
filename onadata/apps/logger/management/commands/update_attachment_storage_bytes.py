#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 fileencoding=utf-8
# coding: utf-8
import json
from collections import defaultdict
from typing import Dict

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import F, Sum

from onadata.apps.logger.models.attachment import Attachment
from onadata.apps.logger.models.xform import XForm
from onadata.apps.main.models.user_profile import UserProfile
from onadata.libs.utils.jsonbfield_helper import ReplaceValues


class Command(BaseCommand):
    help = (
        'Retroactively add the total of '
        'the storage file per xform and user profile'
    )

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
        self.verbosity = kwargs['verbosity']

        # get the max attachments and xforms
        attachments = Attachment.objects.filter(pk__lte=max_pk)
        xforms = (
            XForm.objects.all()
            .values('pk', 'user_id', 'user__username')
            .order_by('user_id')
        )
        max_per_user = defaultdict(int)

        last_xform = None
        for xform in xforms:
            # we don't need to lock the row because it's not exposed in the
            # API and cannot be changed

            if not last_xform or (last_xform['user_id'] != xform['user_id']):
                # retrieve or create user's profile
                (
                    user_profile,
                    created,
                ) = UserProfile.objects.get_or_create(
                    user_id=xform['user_id']
                )

                # if flag is set to false, no need to go further
                if user_profile.metadata.get('submissions_suspended') is False:
                    if self.verbosity > 1:
                        self.stdout.write(
                            f"Profile for user {xform['user__username']} "
                            f"#{xform['user_id']} has already been updated"
                        )
                    continue

                # Set the flag to true if it was never set
                if not user_profile.metadata.get('submissions_suspended'):
                    # we are using the flag `submissions_suspended` to prevent
                    # new submissions from coming in while the
                    # `attachment_storage_bytes` is being calculated
                    user_profile.metadata['submissions_suspended'] = True
                    # we use this temporary list to keep track of which forms
                    # have been calculated in case the command is disrupted
                    user_profile.metadata['xforms_in_progress'] = []
                    # Only update metadata to avoid overwriting other fields
                    # (such as "num_of_submissions") if another concurrent query
                    # runs on this particular row.
                    user_profile.save(update_fields=['metadata'])
                    if self.verbosity > 2:
                        self.stdout.write(
                            f"Metadata for user {xform['user__username']} "
                            f"#{xform['user_id']}"
                        )
                        self.stdout.write(json.dumps(user_profile.metadata))

                # if `last_xform` is not none, it means that the `user_id` is
                # different from the previous one in the loop so the user
                # profile must be updated
                if last_xform:
                    self.update_user_profile(
                        last_xform, max_per_user[last_xform['user_id']]
                    )

            # write out xform progress
            if self.verbosity >= 1:
                self.stdout.write(
                    f"Calculating attachments for xform_id #{xform['pk']}"
                    f"/ user {xform['user__username']}"
                )
            # aggregate total media file size for all media per xform
            form_attachments = attachments.filter(
                instance__xform_id=xform['pk']
            ).aggregate(total=Sum('media_file_size'))

            if form_attachments['total']:

                if xform['pk'] not in user_profile.metadata['xforms_in_progress']:
                    with transaction.atomic():
                        XForm.objects.select_for_update().filter(
                            pk=xform['pk']
                        ).update(
                            attachment_storage_bytes=F(
                                'attachment_storage_bytes'
                            )
                            + form_attachments['total']
                        )
                    # Ensure we have an updated list of xform ids already
                    # updated before updating `xforms_in_progress` property
                    user_profile.refresh_from_db()
                    xform_ids = user_profile.metadata['xforms_in_progress']
                    xform_ids.append(xform['pk'])
                    # A bit of paranoia here because, as said above, `metadata` is
                    # not exposed publicly, but let's only update
                    # `xforms_in_progress` property in `metadata` JSONBField
                    UserProfile.objects.filter(
                       user_id=xform['user_id']
                    ).update(
                       metadata=ReplaceValues(
                           'metadata',
                           updates={'xforms_in_progress': xform_ids},
                       ),
                    )

                max_per_user[xform['user_id']] += form_attachments['total']

            last_xform = xform

        # need to call `update_user_profile()` one more time outside the loop
        # because the last user profile will not be up-to-date otherwise
        if last_xform:
            self.update_user_profile(
                last_xform, max_per_user[last_xform['user_id']]
            )

        if self.verbosity >= 1:
            self.stdout.write('Done!')

    def update_user_profile(self, xform: Dict, total: int):
        user_id = xform['user_id']
        username = xform['user__username']
        # write out user_id progress
        if self.verbosity >= 1:
            self.stdout.write(
                f'Updating attachment storage total ({total} bytes) to '
                f'{username}’s profile'
            )

        with transaction.atomic():
            updates = {
                'submissions_suspended': False,
                # cleaning up fields that are useless outside this one time
                # use management command
                'xforms_in_progress': [],
            }

            UserProfile.objects.select_for_update().filter(
                user_id=user_id
            ).update(
                attachment_storage_bytes=F('attachment_storage_bytes') + total,
                metadata=ReplaceValues(
                    'metadata',
                    updates=updates,
                ),
            )
