#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 fileencoding=utf-8
# coding: utf-8
from __future__ import unicode_literals, print_function, division, absolute_import

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils.translation import ugettext as _

from onadata.libs.utils.briefcase_client import BriefcaseClient


class Command(BaseCommand):
    help = _("Insert all existing parsed instances into MongoDB")

    def add_arguments(self, parser):
        parser.add_argument('--url',
                            help=_("server url to pull forms and submissions"))

        parser.add_argument('-u', '--username',
                            help=_("Username"))

        parser.add_argument('-p', '--password',
                            help=_("Password"))

        parser.add_argument('--to',
                            help=_("username in this server"))

    def handle(self, *args, **kwargs):
        url = kwargs.get('url')
        username = kwargs.get('username')
        password = kwargs.get('password')
        to = kwargs.get('to')
        user = User.objects.get(username=to)
        bc = BriefcaseClient(username=username, password=password,
                             user=user, url=url)
        bc.download_xforms(include_instances=True)
