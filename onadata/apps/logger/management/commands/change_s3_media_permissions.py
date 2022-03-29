#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 fileencoding=utf-8
# coding: utf-8
import sys

from django.core.management.base import BaseCommand, CommandError
from django.core.files.storage import get_storage_class
from django.utils.translation import gettext as t, gettext_lazy


class Command(BaseCommand):
    help = gettext_lazy("Makes all s3 files private")

    def handle(self, *args, **kwargs):
        permissions = ('private', 'public-read', 'authenticated-read')

        if len(args) < 1:
            raise CommandError(t("Missing permission argument"))

        permission = args[0]

        if permission not in permissions:
            raise CommandError(t(
                "Expected %s as permission") % ' or '.join(permissions))

        try:
            s3 = get_storage_class('storages.backends.s3boto3.S3Boto3Storage')()
        except:
            print(t("Missing necessary libraries. Try running: pip install "
                    "-r requirements-s3.pip"))
            sys.exit(1)
        else:
            all_files = s3.bucket.list()

            for i, f in enumerate(all_files):
                f.set_acl(permission)
                if i % 1000 == 0:
                    print(i, "file objects processed")

            print("a total of", i, "file objects processed")
