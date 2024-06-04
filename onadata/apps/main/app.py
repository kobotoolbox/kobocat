# coding: utf-8
from django.apps import AppConfig


class MainConfig(AppConfig):
    name = 'onadata.apps.main'

    def ready(self):
        from onadata.apps.main import signals
        super().ready()
