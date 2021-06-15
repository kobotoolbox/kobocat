# coding: utf-8
from django.apps import AppConfig


class RestServiceConfig(AppConfig):
    name = "onadata.apps.restservice"
    verbose_name = "restservice"

    def ready(self):
        # Register RestService signals
        import onadata.apps.restservice.signals
