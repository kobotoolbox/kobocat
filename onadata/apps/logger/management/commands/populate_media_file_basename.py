#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
from django.conf import settings
from django.db import connection
from django.db.models import Q, Func
from django.db.models.functions import Substr
from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import ugettext as _, ugettext_lazy
from optparse import make_option

from onadata.apps.logger.models.attachment import Attachment


class SubstrFromPattern(Func):
    function = "SUBSTRING"
    template = "%(function)s(%(expressions)s from '%(pattern)s')"


class Command(BaseCommand):

    help = ugettext_lazy("Updates indexed field `media_file_basename` which is empty or null")
    option_list = BaseCommand.option_list + (
        make_option(
            '--batchsize',
            type='int',
            default=100,
            help=ugettext_lazy("Number of records to process per query")),)

    def handle(self, *args, **kwargs):
        batchsize = kwargs.get("batchsize", 100)
        stop = False
        offset = 0
        while stop is not True:
            limit = offset + batchsize
            attachments_ids = list(Attachment.objects.values_list("id", flat=True)
                                                     .filter(Q(media_file_basename=None) | Q(media_file_basename=""))
                                                     .order_by("id")[offset:limit])
            if attachments_ids:
                self.stdout.write(_("Updating attachments from #{} to #{}\n").format(
                    attachments_ids[0],
                    attachments_ids[-1]))

                Attachment.objects.filter(id__in=attachments_ids)\
                    .update(media_file_basename=SubstrFromPattern("media_file", pattern="/([^/]+)$"))

                offset += batchsize
            else:
                stop = True
