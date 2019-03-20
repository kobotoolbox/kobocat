# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import sys

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.http import urlencode
from django.utils.translation import ugettext_lazy as _

from onadata.apps.viewer.models.parsed_instance import xform_instances


class Command(BaseCommand):

    help = _("Rewrite attachments urls to point to new protected endpoint")

    def handle(self, *args, **kwargs):

        query = {"$and": [
            {"_deleted_at": {"$exists": False}},
            {"_deleted_at": None},
            {"_attachments": {"$ne": ""}},
            {"_attachments": {"$ne": []}}
        ]}

        results = xform_instances.find(query)
        instances_count = results.count()
        done = 0
        if instances_count > 0:
            for instance in results:
                for attachment in instance.get("_attachments"):
                    filename = attachment.get("filename")
                    attachment["download_url"] = self.__secure_url(filename)
                    for suffix in settings.THUMB_CONF.keys():
                        attachment["download_{}_url".format(suffix)] = self.__secure_url(filename, suffix)

                done += 1
                time.sleep(1)

                xform_instances.save(instance)
                sys.stdout.write(
                    "%.2f %% done ...\r" % ((float(done) / float(instances_count)) * 100))

    @staticmethod
    def __secure_url(filename, suffix="original"):
        """
        Returns image URL through kobocat redirector.
        :param filename: str. relative path to filename
        :param suffix: str. original|large|medium|small
        :return: str
        """
        return "{kobocat_url}{media_url}{suffix}?{media_file}".format(
            kobocat_url=settings.KOBOCAT_URL,
            media_url=settings.MEDIA_URL,
            suffix=suffix,
            media_file=urlencode({"media_file": filename})
        )
