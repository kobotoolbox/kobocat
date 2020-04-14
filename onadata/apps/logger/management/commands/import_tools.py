#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 fileencoding=utf-8
# coding: utf-8
from __future__ import unicode_literals, print_function, division, absolute_import

import glob
import os

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import ugettext as _, ugettext_lazy

from onadata.apps.logger.import_tools import import_instances_from_zip
from onadata.apps.logger.models import Instance

IMAGES_DIR = os.path.join(settings.MEDIA_ROOT, "attachments")


class Command(BaseCommand):
    help = ugettext_lazy("Import ODK forms and instances.")

    def handle(self, *args, **kwargs):
        if args.__len__() < 2:
            raise CommandError(_("path(xform instances) username"))
        path = args[0]
        username = args[1]
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(_("Invalid username %s") % username)
        debug = False
        if debug:
            print(_("[Importing XForm Instances from %(path)s]\n")
                  % {'path': path})
            im_count = len(glob.glob(os.path.join(IMAGES_DIR, '*')))
            print(_("Before Parse:"))
            print(_(" --> Images:    %(nb)d") % {'nb': im_count})
            print(_(" --> Instances: %(nb)d")
                  % {'nb': Instance.objects.count()})
        import_instances_from_zip(path, user)
        if debug:
            im_count2 = len(glob.glob(os.path.join(IMAGES_DIR, '*')))
            print(_("After Parse:"))
            print(_(" --> Images:    %(nb)d") % {'nb': im_count2})
            print(_(" --> Instances: %(nb)d")
                  % {'nb': Instance.objects.count()})
