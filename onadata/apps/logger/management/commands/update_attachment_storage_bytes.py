#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 fileencoding=utf-8
# coding: utf-8
from django.core.management.base import BaseCommand
from django.db.models import F, Sum

from onadata.apps.logger.models.attachment import Attachment
from onadata.apps.logger.models.xform import XForm
from onadata.apps.main.models.user_profile import UserProfile


class Command(BaseCommand):
    help = ('Retroactively add the total of '
            'the storage file per xform and user profile')

    def add_arguments(self, parser):
        parser.add_argument('--max', '-m', type=int, help='Max PK of attachments')

    def handle(self, *args, **kwargs):
        if kwargs['max'] is not None:
            max_pk = kwargs['max']
            attachments = Attachment.objects.filter(pk__lte=max_pk)
        else:
            attachments = Attachment.objects.all()

        user_profiles = UserProfile.objects.all().values(
            'pk', 'user__id', 'attachment_storage_bytes'
        )
        xform = XForm.objects.all().values('pk', 'attachment_storage_bytes')

        for profile in user_profiles:
            user_attachments = attachments.filter(
                instance__xform__user=profile['user__id']
            ).aggregate(total=Sum('media_file_size'))
            profiles = user_profiles.filter(pk=profile['pk'])
            profiles.update(
                attachment_storage_bytes=F(
                    'attachment_storage_bytes'
                ) + user_attachments['total']
            )

        for form in xform:
            form_attachments = attachments.filter(
                instance__xform__pk=form['pk']
            ).aggregate(total=Sum('media_file_size'))
            forms = xform.filter(pk=form['pk'])
            forms.update(
                attachment_storage_bytes=F(
                    'attachment_storage_bytes'
                ) + form_attachments['total']
            )
