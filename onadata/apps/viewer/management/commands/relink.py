# coding: utf-8
from __future__ import unicode_literals, print_function, division, absolute_import
from django.core.management.base import BaseCommand
from django.utils.translation import ugettext_lazy
from ...models import Instance


class Command(BaseCommand):
    help = ugettext_lazy("Relink all instances with the current forms.")

    def handle(self, *args, **kwargs):
        for instance in Instance.objects.all():
            instance._link()
            instance.save()
