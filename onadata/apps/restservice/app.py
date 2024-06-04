# coding: utf-8
from django.apps import AppConfig


class RestServiceConfig(AppConfig):
    name = 'onadata.apps.restservice'
    verbose_name = 'restservice'

    def ready(self):
        # Register RestService signals
        from onadata.apps.restservice import signals
        super().ready()
