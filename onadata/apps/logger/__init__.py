# coding: utf-8
from django.apps import AppConfig


class LoggerAppConfig(AppConfig):

    name = 'onadata.apps.logger'

    def ready(self):
        # Makes sure all signal handlers are connected
        from onadata.apps.logger import signals
        super().ready()
