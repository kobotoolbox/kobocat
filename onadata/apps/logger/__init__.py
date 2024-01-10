# coding: utf-8
from django.apps import AppConfig
from django.conf import settings
from django.core.checks import register, Error


class LoggerAppConfig(AppConfig):

    name = 'onadata.apps.logger'

    def ready(self):
        # Makes sure all signal handlers are connected
        from onadata.apps.logger import signals
        # Monkey patch reversion package to insert real user in DB instead of
        # system account superuser.
        from kobo_service_account.utils import reversion_monkey_patch
        reversion_monkey_patch()
        super().ready()


@register()
def check_enketo_redis_main_url(app_configs, **kwargs):
    """
    `ENKETO_REDIS_MAIN_URL` is required to make the app run properly.
    """
    errors = []
    if not settings.CACHES.get('enketo_redis_main'):
        # We need to set `BACKEND` property. Otherwise, this error is shadowed
        # by Django CACHES system checks.
        settings.CACHES['enketo_redis_main']['BACKEND'] = (
            'django.core.cache.backends.dummy.DummyCache'
        )
        errors.append(
            Error(
                f'Please set environment variable `ENKETO_REDIS_MAIN_URL`',
                hint='Enketo Express Redis main URL is missing.',
                obj=settings,
                id='kobo.logger.enketo_redis_main.E001',
            )
        )
    return errors
