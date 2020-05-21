# -*- coding: utf-8 -*-
from datetime import timedelta
import logging
import os

import dj_database_url
from celery.signals import after_setup_logger
from django.utils.six.moves.urllib.parse import quote_plus

from onadata.settings.common import *


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


LOCALE_PATHS = [os.path.join(PROJECT_ROOT, 'locale'), ]

DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'
TEMPLATE_DEBUG = os.environ.get('TEMPLATE_DEBUG', 'True') == 'True'
TEMPLATE_STRING_IF_INVALID = ''


DATABASES = {
    'default': dj_database_url.config(default="sqlite:///%s/db.sqlite3" % PROJECT_ROOT)
}
# Replacement for TransactionMiddleware
DATABASES['default']['ATOMIC_REQUESTS'] = True

MONGO_DATABASE = {
    'HOST': os.environ.get('KOBOCAT_MONGO_HOST', 'mongo'),
    'PORT': int(os.environ.get('KOBOCAT_MONGO_PORT', 27017)),
    'NAME': os.environ.get('KOBOCAT_MONGO_NAME', 'formhub'),
    'USER': os.environ.get('KOBOCAT_MONGO_USER', ''),
    'PASSWORD': os.environ.get('KOBOCAT_MONGO_PASS', '')
}

CELERY_BROKER_URL = os.environ.get(
    'KOBOCAT_BROKER_URL', 'amqp://guest:guest@rabbit:5672/')

CELERY_RESULT_BACKEND = CELERY_BROKER_URL

try:
    SECRET_KEY = os.environ['DJANGO_SECRET_KEY']
except KeyError:
    raise Exception('DJANGO_SECRET_KEY must be set in the environment.')

ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '*').split(' ')

TESTING_MODE = False
# This trick works only when we run tests from the command line.
if len(sys.argv) >= 2 and (sys.argv[1] == "test"):
    raise Exception(
        "Testing destroys data and must NOT be run in a production "
        "environment. Please use a different settings file if you want to "
        "run tests."
    )
    TESTING_MODE = True
else:
    TESTING_MODE = False

MEDIA_URL = '/' + os.environ.get('KOBOCAT_MEDIA_URL', 'media').strip('/') + '/'
STATIC_URL = '/static/'
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/login_redirect/'

if os.environ.get('KOBOCAT_ROOT_URI_PREFIX'):
    KOBOCAT_ROOT_URI_PREFIX = '/' + os.environ['KOBOCAT_ROOT_URI_PREFIX'].strip('/') + '/'
    MEDIA_URL = KOBOCAT_ROOT_URI_PREFIX + MEDIA_URL.lstrip('/')
    STATIC_URL = KOBOCAT_ROOT_URI_PREFIX + STATIC_URL.lstrip('/')
    LOGIN_URL = KOBOCAT_ROOT_URI_PREFIX + LOGIN_URL.lstrip('/')
    LOGIN_REDIRECT_URL = KOBOCAT_ROOT_URI_PREFIX + LOGIN_REDIRECT_URL.lstrip('/')

if TESTING_MODE:
    MEDIA_ROOT = os.path.join(PROJECT_ROOT, 'test_media/')
    subprocess.call(["rm", "-r", MEDIA_ROOT])
    MONGO_DATABASE['NAME'] = "formhub_test"
    CELERY_TASK_ALWAYS_EAGER = True
    BROKER_BACKEND = 'memory'
    ENKETO_API_TOKEN = 'abc'
    #TEST_RUNNER = 'djcelery.contrib.test_runner.CeleryTestSuiteRunner'
else:
    MEDIA_ROOT = os.path.join(PROJECT_ROOT, MEDIA_URL.lstrip('/'))

if PRINT_EXCEPTION and DEBUG:
    MIDDLEWARE_CLASSES += ('utils.middleware.ExceptionLoggingMiddleware',)

# Clear out the test database
if TESTING_MODE:
    MONGO_DB.instances.drop()

# include the kobocat-template directory
TEMPLATE_OVERRIDE_ROOT_DIR = os.environ.get(
    'KOBOCAT_TEMPLATES_PATH',
    os.path.abspath(os.path.join(PROJECT_ROOT, 'kobocat-template'))
)
TEMPLATE_DIRS = (os.path.join(TEMPLATE_OVERRIDE_ROOT_DIR, 'templates'), ) + TEMPLATE_DIRS
STATICFILES_DIRS += (os.path.join(TEMPLATE_OVERRIDE_ROOT_DIR, 'static'), )

KOBOFORM_SERVER = os.environ.get("KOBOFORM_SERVER", "localhost")
KOBOFORM_SERVER_PORT = os.environ.get("KOBOFORM_SERVER_PORT", "8000")
KOBOFORM_SERVER_PROTOCOL = os.environ.get("KOBOFORM_SERVER_PROTOCOL", "http")
KOBOFORM_LOGIN_AUTOREDIRECT = True
KOBOFORM_URL = os.environ.get("KOBOFORM_URL", "http://kf.kobo.local")
KOBOCAT_URL = os.environ.get("KOBOCAT_URL", "http://kc.kobo.local")


TEMPLATE_CONTEXT_PROCESSORS = (
    'onadata.koboform.context_processors.koboform_integration',
) + TEMPLATE_CONTEXT_PROCESSORS

MIDDLEWARE_CLASSES = ('onadata.koboform.redirect_middleware.ConditionalRedirects', ) + MIDDLEWARE_CLASSES

# Domain must not exclude KPI when sharing sessions
if os.environ.get('SESSION_COOKIE_DOMAIN'):
    SESSION_COOKIE_DOMAIN = os.environ['SESSION_COOKIE_DOMAIN']
    SESSION_COOKIE_NAME = 'kobonaut'

SESSION_SERIALIZER = 'django.contrib.sessions.serializers.JSONSerializer'

# for debugging
# print "KOBOFORM_URL=%s" % KOBOFORM_URL
# print "SECRET_KEY=%s" % SECRET_KEY
# print "CSRF_COOKIE_DOMAIN=%s " % CSRF_COOKIE_DOMAIN

# MongoDB - moved here from common.py
if MONGO_DATABASE.get('USER') and MONGO_DATABASE.get('PASSWORD'):
    MONGO_CONNECTION_URL = "mongodb://{user}:{password}@{host}:{port}/{db_name}".\
        format(
            user=MONGO_DATABASE['USER'],
            password=quote_plus(MONGO_DATABASE['PASSWORD']),
            host=MONGO_DATABASE['HOST'],
            port=MONGO_DATABASE['PORT'],
            db_name=MONGO_DATABASE['NAME']
        )
else:
    MONGO_CONNECTION_URL = "mongodb://%(HOST)s:%(PORT)s/%(NAME)s" % MONGO_DATABASE

# PyMongo 3 does acknowledged writes by default
# https://emptysqua.re/blog/pymongos-new-default-safe-writes/
MONGO_CONNECTION = MongoClient(
    MONGO_CONNECTION_URL, j=True, tz_aware=True)

MONGO_DB = MONGO_CONNECTION[MONGO_DATABASE['NAME']]

# BEGIN external service integration codes
AWS_ACCESS_KEY_ID = os.environ.get('KOBOCAT_AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('KOBOCAT_AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.environ.get('KOBOCAT_AWS_STORAGE_BUCKET_NAME')
AWS_DEFAULT_ACL = 'private'
AWS_S3_FILE_BUFFER_SIZE = 50 * 1024 * 1024
# TODO pass these variables from `kobo-docker` envfiles
AWS_QUERYSTRING_EXPIRE = os.environ.get("KOBOCAT_AWS_QUERYSTRING_EXPIRE", 3600)
AWS_S3_USE_SSL = os.environ.get("KOBOCAT_AWS_S3_USE_SSL", True)
AWS_S3_HOST = os.environ.get("KOBOCAT_AWS_S3_HOST", "s3.amazonaws.com")


GOOGLE_ANALYTICS_PROPERTY_ID = os.environ.get("GOOGLE_ANALYTICS_TOKEN", False)
GOOGLE_ANALYTICS_DOMAIN = "auto"
# END external service integration codes

# If not properly overridden, leave uninitialized so Django can set the default.
# (see https://docs.djangoproject.com/en/1.8/ref/settings/#default-file-storage)
if os.environ.get('KOBOCAT_DEFAULT_FILE_STORAGE'):
    DEFAULT_FILE_STORAGE = os.environ.get('KOBOCAT_DEFAULT_FILE_STORAGE')

EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND',
    'django.core.mail.backends.filebased.EmailBackend')

if EMAIL_BACKEND == 'django.core.mail.backends.filebased.EmailBackend':
    EMAIL_FILE_PATH = os.environ.get(
        'EMAIL_FILE_PATH', os.path.join(PROJECT_ROOT, 'emails'))
    if not os.path.isdir(EMAIL_FILE_PATH):
        os.mkdir(EMAIL_FILE_PATH)

# Default value for the `UserProfile.require_auth` attribute
REQUIRE_AUTHENTICATION_TO_SEE_FORMS_AND_SUBMIT_DATA_DEFAULT = os.environ.get(
        'REQUIRE_AUTHENTICATION_TO_SEE_FORMS_AND_SUBMIT_DATA_DEFAULT',
        'False') == 'True'

# Optional Sentry configuration: if desired, be sure to install Raven and set
# RAVEN_DSN in the environment
if (os.getenv("RAVEN_DSN") or "") != "":
    try:
        import raven
    except ImportError:
        print('Please install Raven to enable Sentry logging.')
    else:
        INSTALLED_APPS = INSTALLED_APPS + (
            'raven.contrib.django.raven_compat',
        )
        RAVEN_CONFIG = {
            'dsn': os.environ['RAVEN_DSN'],
        }

        # Set the `server_name` attribute. See https://docs.sentry.io/hosted/clients/python/advanced/
        server_name = os.environ.get('RAVEN_SERVER_NAME')
        server_name = server_name or '.'.join(filter(None, (
            os.environ.get('KOBOCAT_PUBLIC_SUBDOMAIN', None),
            os.environ.get('PUBLIC_DOMAIN_NAME', None)
        )))
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

POSTGIS_VERSION = (2, 5, 0)

CELERY_BEAT_SCHEDULE = {
    # Periodically mark exports stuck in the "pending" state as "failed"
    # See https://github.com/kobotoolbox/kobocat/issues/315
    'log-stuck-exports-and-mark-failed': {
        'task': 'onadata.apps.viewer.tasks.log_stuck_exports_and_mark_failed',
        'schedule': timedelta(hours=6),
        'options': {'queue': 'kobocat_queue'}
    },
}

# ## ISSUE 242 TEMPORARY FIX ###
# See https://github.com/kobotoolbox/kobocat/issues/242
ISSUE_242_MINIMUM_INSTANCE_ID = os.environ.get(
    'ISSUE_242_MINIMUM_INSTANCE_ID', None)
ISSUE_242_INSTANCE_XML_SEARCH_STRING = os.environ.get(
    'ISSUE_242_INSTANCE_XML_SEARCH_STRING', 'uploaded_form_')
if ISSUE_242_MINIMUM_INSTANCE_ID is not None:
    CELERY_BEAT_SCHEDULE['fix-root-node-names'] = {
        'task': 'onadata.apps.logger.tasks.fix_root_node_names',
        'schedule': timedelta(hours=1),
        'kwargs': {
            'pk__gte': int(ISSUE_242_MINIMUM_INSTANCE_ID),
            'xml__contains': ISSUE_242_INSTANCE_XML_SEARCH_STRING
        },
        'options': {'queue': 'kobocat_queue'}
    }

###### END ISSUE 242 FIX ######
