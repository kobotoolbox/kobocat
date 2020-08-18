# coding: utf-8
from datetime import timedelta


from celery.signals import after_setup_logger

from .base import *


def celery_logger_setup_handler(logger, **kwargs):
    """
    Allows logs to be written in celery.log when call
    :param logger:
    :param kwargs:
    """
    my_handler = logging.FileHandler(os.getenv("KOBOCAT_CELERY_LOG_FILE", "/srv/logs/celery.log"))
    my_handler.setLevel(logging.INFO)
    my_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')  # custom formatter
    my_handler.setFormatter(my_formatter)
    logger.addHandler(my_handler)


if os.environ.get('KOBOCAT_ROOT_URI_PREFIX'):
    KOBOCAT_ROOT_URI_PREFIX = '/' + os.environ['KOBOCAT_ROOT_URI_PREFIX'].strip('/') + '/'
    MEDIA_URL = KOBOCAT_ROOT_URI_PREFIX + MEDIA_URL.lstrip('/')
    STATIC_URL = KOBOCAT_ROOT_URI_PREFIX + STATIC_URL.lstrip('/')
    LOGIN_URL = KOBOCAT_ROOT_URI_PREFIX + LOGIN_URL.lstrip('/')
    LOGIN_REDIRECT_URL = KOBOCAT_ROOT_URI_PREFIX + LOGIN_REDIRECT_URL.lstrip('/')

MEDIA_ROOT = os.path.join(PROJECT_ROOT, MEDIA_URL.lstrip('/'))

# Optional Sentry configuration: if desired, be sure to install Raven and set
# RAVEN_DSN in the environment
if (os.getenv("RAVEN_DSN") or "") != "":
    try:
        import raven
    except ImportError:
        print('Please install Raven to enable Sentry logging.')
    else:
        INSTALLED_APPS.append('raven.contrib.django.raven_compat')
        RAVEN_CONFIG = {
            'dsn': os.environ['RAVEN_DSN'],
        }

        # Set the `server_name` attribute. See https://docs.sentry.io/hosted/clients/python/advanced/
        server_name = os.environ.get('RAVEN_SERVER_NAME')
        server_name = server_name or '.'.join([_f for _f in (
            os.environ.get('KOBOCAT_PUBLIC_SUBDOMAIN', None),
            os.environ.get('PUBLIC_DOMAIN_NAME', None)
        ) if _f])

        if server_name:
            RAVEN_CONFIG.update({'name': server_name})

        try:
            RAVEN_CONFIG['release'] = raven.fetch_git_sha(BASE_DIR)
        except raven.exceptions.InvalidGitRepository:
            pass

        # The below is NOT required for Sentry to log unhandled exceptions, but it
        # is necessary for capturing messages sent via the `logging` module.
        # https://docs.getsentry.com/hosted/clients/python/integrations/django/#integration-with-logging
        LOGGING = {
            'version': 1,
            'disable_existing_loggers': True,  # Follows Sentry docs; `False` contributes to a deadlock (issue #377)
            'root': {
                'level': 'WARNING',
                'handlers': ['sentry'],
            },
            'formatters': {
                'verbose': {
                    'format': '%(levelname)s %(asctime)s %(module)s '
                              '%(process)d %(thread)d %(message)s'
                },
            },
            'handlers': {
                'sentry': {
                    'level': 'WARNING',
                    'class': 'raven.contrib.django.raven_compat.handlers.SentryHandler',
                },
                'console': {
                    'level': 'DEBUG',
                    'class': 'logging.StreamHandler',
                    'formatter': 'verbose'
                }
            },
            'loggers': {
                'django.db.backends': {
                    'level': 'ERROR',
                    'handlers': ['console'],
                    'propagate': False,
                },
                'raven': {
                    'level': 'DEBUG',
                    'handlers': ['console'],
                    'propagate': False,
                },
                'console_logger': {
                    'handlers': ['console'],
                    'level': 'DEBUG',
                    'propagate': True
                },
                'sentry.errors': {
                    'level': 'DEBUG',
                    'handlers': ['console'],
                    'propagate': False,
                },
            },
        }
        CELERY_WORKER_HIJACK_ROOT_LOGGER = False
        after_setup_logger.connect(celery_logger_setup_handler)

SESSION_ENGINE = "redis_sessions.session"
SESSION_REDIS = RedisHelper.config(default="redis://redis_cache:6380/2")
