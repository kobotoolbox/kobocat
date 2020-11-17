# coding: utf-8
from __future__ import unicode_literals, print_function, division, absolute_import

from django.apps import AppConfig


class RestServiceConfig(AppConfig):
    name = "onadata.apps.restservice"
    verbose_name = "restservice"

    def ready(self):
        # Register RestService signals
        import onadata.apps.restservice.signals
