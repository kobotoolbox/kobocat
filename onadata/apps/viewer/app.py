# coding: utf-8
from django.apps import AppConfig


class ViewerConfig(AppConfig):
    name = 'onadata.apps.viewer'

    def ready(self):
        from onadata.apps.viewer import signals
        super().ready()
