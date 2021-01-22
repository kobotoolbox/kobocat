# coding: utf-8
import logging
import multiprocessing
import os
import sys
from datetime import timedelta
from urllib.parse import quote_plus

import dj_database_url
from django.core.exceptions import SuspiciousOperation
from pymongo import MongoClient


def skip_suspicious_operations(record):
    """Prevent django from sending 500 error
    email notifications for SuspiciousOperation
    events, since they are not true server errors,
    especially when related to the ALLOWED_HOSTS
    configuration

    background and more information:
    http://www.tiwoc.de/blog/2013/03/django-prevent-email-notification-on-suspiciousoperation/
    """
    if record.exc_info:
        exc_value = record.exc_info[1]
        if isinstance(exc_value, SuspiciousOperation):
            return False
    return True


BASE_DIR = os.path.dirname(os.path.dirname(__file__))
ONADATA_DIR = BASE_DIR
PROJECT_ROOT = os.path.abspath(os.path.join(ONADATA_DIR, '..'))

################################
# Django Framework settings    #
################################

# Django `SECRET_KEY`
try:
    SECRET_KEY = os.environ['DJANGO_SECRET_KEY']
except KeyError:
    raise Exception('DJANGO_SECRET_KEY must be set in the environment.')

TEMPLATED_EMAIL_TEMPLATE_DIR = 'templated_email/'

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)
MANAGERS = ADMINS


DEFAULT_FROM_EMAIL = 'noreply@kobotoolbox.org'
DEFAULT_SESSION_EXPIRY_TIME = 21600  # 6 hours

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/New_York'
USE_TZ = True

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = os.environ.get('DJANGO_SITE_ID', '1')

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = f"/{os.environ.get('KOBOCAT_MEDIA_URL', 'media').strip('/')}/"

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = os.path.join(ONADATA_DIR, 'static')

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Login URLs
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/login_redirect/'


if os.environ.get('KOBOCAT_ROOT_URI_PREFIX'):
    KOBOCAT_ROOT_URI_PREFIX = '/' + os.environ['KOBOCAT_ROOT_URI_PREFIX'].strip('/') + '/'
    MEDIA_URL = KOBOCAT_ROOT_URI_PREFIX + MEDIA_URL.lstrip('/')
    STATIC_URL = KOBOCAT_ROOT_URI_PREFIX + STATIC_URL.lstrip('/')
    LOGIN_URL = KOBOCAT_ROOT_URI_PREFIX + LOGIN_URL.lstrip('/')
    LOGIN_REDIRECT_URL = KOBOCAT_ROOT_URI_PREFIX + LOGIN_REDIRECT_URL.lstrip('/')

MEDIA_ROOT = os.path.join(PROJECT_ROOT, MEDIA_URL.lstrip('/'))

# URL prefix for admin static files -- CSS, JavaScript and images.
# Make sure to use a trailing slash.
# Examples: "http://foo.com/static/admin/", "/static/admin/".
ADMIN_MEDIA_PREFIX = '/static/admin/'

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

MIDDLEWARE = [
    'onadata.koboform.redirect_middleware.ConditionalRedirects',
    'reversion.middleware.RevisionMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'onadata.libs.utils.middleware.LocaleMiddlewareWithTweaks',
    'django.middleware.csrf.CsrfViewMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'onadata.libs.utils.middleware.HTTPResponseNotAllowedMiddleware',
    'readonly.middleware.DatabaseReadOnlyMiddleware',
    'onadata.libs.utils.middleware.UsernameInResponseHeaderMiddleware',
]

ROOT_URLCONF = 'onadata.apps.main.urls'

# specify the root folder which may contain a templates folder and a static
# folder used to override templates for site specific details
# include the kobocat-template directory
TEMPLATE_OVERRIDE_ROOT_DIR = os.environ.get(
    'KOBOCAT_TEMPLATES_PATH',
    os.path.abspath(os.path.join(PROJECT_ROOT, 'kobocat-template'))
)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': False,
        'DIRS': [
            os.path.join(TEMPLATE_OVERRIDE_ROOT_DIR, 'templates'),
            os.path.join(ONADATA_DIR, 'libs/templates')
        ],
        'OPTIONS': {
            'context_processors': [
                'onadata.koboform.context_processors.koboform_integration',
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.template.context_processors.request',
                'django.contrib.messages.context_processors.messages',
                'readonly.context_processors.readonly',
                'onadata.apps.main.context_processors.google_analytics',
                'onadata.apps.main.context_processors.site_name',
                'onadata.apps.main.context_processors.base_url'
            ],
            'loaders': [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
            ],
            'debug': os.environ.get('TEMPLATE_DEBUG', 'False') == 'True',
        },
    }
]

DIRS = [
    os.path.join(TEMPLATE_OVERRIDE_ROOT_DIR, 'templates'),
    os.path.join(ONADATA_DIR, 'libs/templates'),
]

# Additional locations of static files
STATICFILES_DIRS = [
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(TEMPLATE_OVERRIDE_ROOT_DIR, 'static')
]

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    # Always put `contenttypes` before `auth`; see
    # https://code.djangoproject.com/ticket/10827
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'django.contrib.admin',
    'django.contrib.admindocs',
    'django.contrib.gis',
    'registration',
    'reversion',
    'django_digest',
    'corsheaders',
    'oauth2_provider',
    'rest_framework',
    'rest_framework.authtoken',
    'taggit',
    'readonly',
    'onadata.apps.logger',
    'onadata.apps.viewer',
    'onadata.apps.main',
    'onadata.apps.restservice',
    'onadata.apps.api',
    'guardian',
    'onadata.libs',
    'pure_pagination',
    'django_celery_beat',
    'django_extensions',
]

USE_THOUSAND_SEPARATOR = True

COMPRESS = True

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s' +
                      ' %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        },
        # Define filter for suspicious urls
        'skip_suspicious_operations': {
            '()': 'django.utils.log.CallbackFilter',
            'callback': skip_suspicious_operations,
        },
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false', 'skip_suspicious_operations'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
            'stream': sys.stdout
        },
        'audit': {
            'level': 'DEBUG',
            'class': 'onadata.libs.utils.log.AuditLogHandler',
            'formatter': 'verbose',
            'model': 'onadata.apps.main.models.audit.AuditLog'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'console_logger': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True
        },
        'audit_logger': {
            'handlers': ['audit'],
            'level': 'DEBUG',
            'propagate': True
        }
    }
}

# extra data stored with users
AUTH_PROFILE_MODULE = 'onadata.apps.main.UserProfile'

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'guardian.backends.ObjectPermissionBackend',
)

# Make Django use NGINX $host. Useful when running with ./manage.py runserver_plus
# It avoids adding the debugger webserver port (i.e. `:8000`) at the end of urls.
if os.getenv("USE_X_FORWARDED_HOST", "False") == "True":
    USE_X_FORWARDED_HOST = True

# "Although the setting offers little practical benefit, it's sometimes
# required by security auditors."
# -- https://docs.djangoproject.com/en/2.2/ref/settings/#csrf-cookie-httponly
CSRF_COOKIE_HTTPONLY = True
# SESSION_COOKIE_HTTPONLY is more useful, but it defaults to True.

if os.environ.get('PUBLIC_REQUEST_SCHEME', '').lower() == 'https':
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# Limit sessions to 1 week (the default is 2 weeks)
SESSION_COOKIE_AGE = 604800

# The maximum size in bytes that a request body may be before a SuspiciousOperation (RequestDataTooBig) is raised
# This variable is available only in Django 1.10+. Only there for next upgrade
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760

# The maximum size (in bytes) that an upload will be before it gets streamed to the file system
FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760

LOCALE_PATHS = [os.path.join(PROJECT_ROOT, 'locale'), ]

DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'

# Database (i.e. PostgreSQL)
DATABASES = {
    'default': dj_database_url.config(default="sqlite:///%s/db.sqlite3" % PROJECT_ROOT)
}
# Replacement for TransactionMiddleware
DATABASES['default']['ATOMIC_REQUESTS'] = True

ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '*').split(' ')

# Domain must not exclude KPI when sharing sessions
if os.environ.get('SESSION_COOKIE_DOMAIN'):
    SESSION_COOKIE_DOMAIN = os.environ['SESSION_COOKIE_DOMAIN']
    SESSION_COOKIE_NAME = 'kobonaut'

SESSION_SERIALIZER = 'django.contrib.sessions.serializers.JSONSerializer'

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


###################################
# Django Rest Framework settings  #
###################################

REST_FRAMEWORK = {
    # Use hyperlinked styles by default.
    # Only used if the `serializer_class` attribute is not set on a view.
    'DEFAULT_MODEL_SERIALIZER_CLASS':
    'rest_framework.serializers.HyperlinkedModelSerializer',

    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'onadata.libs.authentication.DigestAuthentication',
        'oauth2_provider.contrib.rest_framework.OAuth2Authentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
        'onadata.libs.authentication.HttpsOnlyBasicAuthentication',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        # Keep JSONRenderer at the top "in order to send JSON responses to
        # clients that do not specify an Accept header." See
        # http://www.django-rest-framework.org/api-guide/renderers/#ordering-of-renderer-classes
        'rest_framework.renderers.JSONRenderer',
        'rest_framework_jsonp.renderers.JSONPRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
        'rest_framework_xml.renderers.XMLRenderer',
        'rest_framework_csv.renderers.CSVRenderer',
    ),
    'VIEW_NAME_FUNCTION': 'onadata.apps.api.tools.get_view_name',
    'VIEW_DESCRIPTION_FUNCTION': 'onadata.apps.api.tools.get_view_description',
}

################################
# KoBoCAT settings             #
################################

TESTING_MODE = False

# needed by guardian`
# Deprecated since v1.4.2. ToDo move to constants.py`
ANONYMOUS_USER_ID = -1
# Needed to get ANONYMOUS_USER = -1
GUARDIAN_GET_INIT_ANONYMOUS_USER = 'onadata.apps.main.models.user_profile.get_anonymous_user_instance'  # noqa

PRINT_EXCEPTION = os.environ.get("PRINT_EXCEPTION", False)

KOBOCAT_URL = os.environ.get('KOBOCAT_URL', 'http://kc.kobo.local')
KOBOFORM_SERVER = os.environ.get('KOBOFORM_SERVER', 'localhost')
KOBOFORM_SERVER_PORT = os.environ.get('KOBOFORM_SERVER_PORT', '8000')
KOBOFORM_SERVER_PROTOCOL = os.environ.get('KOBOFORM_SERVER_PROTOCOL', 'http')
KOBOFORM_LOGIN_AUTOREDIRECT = True
KOBOFORM_URL = os.environ.get('KOBOFORM_URL', 'http://kf.kobo.local')
KOBOFORM_INTERNAL_URL = os.environ.get('KOBOFORM_INTERNAL_URL', KOBOFORM_URL)
KPI_HOOK_ENDPOINT_PATTERN = '/api/v2/assets/{asset_uid}/hook-signal/'

# These 2 variables are needed to detect whether the ENKETO_PROTOCOL should overwritten or not.
# See method `_get_form_url` in `onadata/libs/utils/viewer_tools.py`
KOBOCAT_INTERNAL_HOSTNAME = '{}.{}'.format(
    os.environ.get('KOBOCAT_PUBLIC_SUBDOMAIN', 'kc'),
    os.environ.get('INTERNAL_DOMAIN_NAME', 'docker.internal'))
KOBOCAT_PUBLIC_HOSTNAME = '{}.{}'.format(
    os.environ.get('KOBOCAT_PUBLIC_SUBDOMAIN', 'kc'),
    os.environ.get('PUBLIC_DOMAIN_NAME', 'kobotoolbox.org'))

# Default value for the `UserProfile.require_auth` attribute
REQUIRE_AUTHENTICATION_TO_SEE_FORMS_AND_SUBMIT_DATA_DEFAULT = os.environ.get(
        'REQUIRE_AUTHENTICATION_TO_SEE_FORMS_AND_SUBMIT_DATA_DEFAULT',
        'False') == 'True'

OAUTH2_PROVIDER = {
    # this is the list of available scopes
    'SCOPES': {
        'read': 'Read scope',
        'write': 'Write scope',
        'groups': 'Access to your groups'}
}

# All registration should be done through KPI, so Django Registration should
# never be enabled here. It'd be best to remove all references to the
# `registration` app in the future.
REGISTRATION_OPEN = False
ACCOUNT_ACTIVATION_DAYS = 1

SWAGGER_SETTINGS = {
    'exclude_namespaces': [],    # List URL namespaces to ignore
    'api_version': '1.0',  # Specify your API's version (optional)
    'enabled_methods': [         # Methods to enable in UI
        'get',
        'post',
        'put',
        'patch',
        'delete'
    ],
}

# CORS policies
CORS_ORIGIN_ALLOW_ALL = False
CORS_ALLOW_CREDENTIALS = True
CORS_ORIGIN_WHITELIST = (
    'http://kc.kobo.local',
)

# ToDo Remove when `kobokitten-remove-ui-CUD-actions-unicode` is merged
GOOGLE_STEP2_URI = 'http://ona.io/gwelcome'
GOOGLE_CLIENT_ID = '617113120802.onadata.apps.googleusercontent.com'
GOOGLE_CLIENT_SECRET = '9reM29qpGFPyI8TBuB54Z4fk'

THUMB_CONF = {
    'large': {'size': 1280, 'suffix': '-large'},
    'medium': {'size': 640, 'suffix': '-medium'},
    'small': {'size': 240, 'suffix': '-small'},
}
# order of thumbnails from largest to smallest
THUMB_ORDER = ['large', 'medium', 'small']

# Number of times Celery retries to send data to external rest service
REST_SERVICE_MAX_RETRIES = 3

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
# duration to keep zip exports before deletion (in seconds)
ZIP_EXPORT_COUNTDOWN = 24 * 60 * 60

# default content length for submission requests
DEFAULT_CONTENT_LENGTH = 10000000

# TODO pass these variables from `kobo-docker` envfiles
# re-captcha in registrations
REGISTRATION_REQUIRE_CAPTCHA = False
RECAPTCHA_USE_SSL = False
RECAPTCHA_PRIVATE_KEY = ''
RECAPTCHA_PUBLIC_KEY = '6Ld52OMSAAAAAJJ4W-0TFDTgbznnWWFf0XuOSaB6'

# Use 1 or 0 for multiple selects instead of True or False for csv, xls exports
BINARY_SELECT_MULTIPLES = False

# Use 'n/a' for empty values by default on csv exports
NA_REP = 'n/a'

SUPPORTED_MEDIA_UPLOAD_TYPES = [
    'image/jpeg',
    'image/png',
    'image/svg+xml',
    'video/3gpp',
    'video/mp4',
    'video/quicktime',
    'video/ogg',
    'video/webm',
    'audio/aac',
    'audio/aacp',
    'audio/flac',
    'audio/mp3',
    'audio/mp4',
    'audio/mpeg',
    'audio/ogg',
    'audio/wav',
    'audio/webm',
    'audio/x-m4a',
    'text/csv',
    'application/zip'
]

DEFAULT_VALIDATION_STATUSES = [
    {
        'uid': 'validation_status_not_approved',
        'color': '#ff0000',
        'label': 'Not Approved'
    },
    {
        'uid': 'validation_status_approved',
        'color': '#00ff00',
        'label': 'Approved'
    },
    {
        'uid': 'validation_status_on_hold',
        'color': '#0000ff',
        'label': 'On Hold'
    },
]

################################
# Celery settings              #
################################

CELERY_BROKER_URL = os.environ.get(
    'KOBOCAT_BROKER_URL', 'redis://localhost:6389/2')

CELERY_RESULT_BACKEND = CELERY_BROKER_URL

CELERY_TASK_ALWAYS_EAGER = os.environ.get('SKIP_CELERY', 'False') == 'True'

# Celery defaults to having as many workers as there are cores. To avoid
# excessive resource consumption, don't spawn more than 6 workers by default
# even if there more than 6 cores.
CELERY_WORKER_MAX_CONCURRENCY = int(os.environ.get('CELERYD_MAX_CONCURRENCY', 6))
if multiprocessing.cpu_count() > CELERY_WORKER_MAX_CONCURRENCY:
    CELERY_WORKER_CONCURRENCY = CELERY_WORKER_MAX_CONCURRENCY

# Replace a worker after it completes 7 tasks by default. This allows the OS to
# reclaim memory allocated during large tasks
CELERY_WORKER_MAX_TASKS_PER_CHILD = int(os.environ.get(
    'CELERYD_MAX_TASKS_PER_CHILD', 7))

# Default to a 30-minute soft time limit and a 35-minute hard time limit
CELERY_TASK_TIME_LIMIT = int(os.environ.get('CELERY_TASK_TIME_LIMIT', 2100))
CELERY_TASK_SOFT_TIME_LIMIT = int(os.environ.get(
    'CELERYD_TASK_SOFT_TIME_LIMIT', 1800))

CELERY_BROKER_TRANSPORT_OPTIONS = {
    "fanout_patterns": True,
    "fanout_prefix": True,
    # http://docs.celeryproject.org/en/latest/getting-started/brokers/redis.html#redis-visibility-timeout
    "visibility_timeout": 120 * (10 ** REST_SERVICE_MAX_RETRIES)  # Longest ETA for RestService
}

CELERY_BEAT_SCHEDULE = {
    # Periodically mark exports stuck in the "pending" state as "failed"
    # See https://github.com/kobotoolbox/kobocat/issues/315
    'log-stuck-exports-and-mark-failed': {
        'task': 'onadata.apps.viewer.tasks.log_stuck_exports_and_mark_failed',
        'schedule': timedelta(hours=6),
        'options': {'queue': 'kobocat_queue'}
    },
}

CELERY_TASK_DEFAULT_QUEUE = "kobocat_queue"


################################
# Enketo Express settings      #
################################

ENKETO_URL = os.environ.get('ENKETO_URL', 'https://enketo.kobotoolbox.org')

ENKETO_URL = ENKETO_URL.rstrip('/')
ENKETO_API_TOKEN = os.environ.get('ENKETO_API_TOKEN', 'enketorules')
ENKETO_VERSION = 'express'

# Constants.
ENKETO_API_ENDPOINT_ONLINE_SURVEYS = '/survey'
ENKETO_API_ENDPOINT_OFFLINE_SURVEYS = '/survey/offline'
ENKETO_API_ENDPOINT_INSTANCE = '/instance'
ENKETO_API_ENDPOINT_INSTANCE_IFRAME = '/instance/iframe'

# Computed settings.
ENKETO_API_ROOT = '/api/v2'
ENKETO_OFFLINE_SURVEYS = os.environ.get('ENKETO_OFFLINE_SURVEYS', 'True').lower() == 'true'
ENKETO_API_ENDPOINT_PREVIEW = '/preview'
ENKETO_API_ENDPOINT_SURVEYS = ENKETO_API_ENDPOINT_OFFLINE_SURVEYS if ENKETO_OFFLINE_SURVEYS \
        else ENKETO_API_ENDPOINT_ONLINE_SURVEYS

ENKETO_API_SURVEY_PATH = ENKETO_API_ROOT + ENKETO_API_ENDPOINT_SURVEYS
ENKETO_API_INSTANCE_PATH = ENKETO_API_ROOT + ENKETO_API_ENDPOINT_INSTANCE
ENKETO_PREVIEW_URL = ENKETO_URL + ENKETO_API_ENDPOINT_PREVIEW
ENKETO_API_INSTANCE_IFRAME_URL = ENKETO_URL + ENKETO_API_ROOT + ENKETO_API_ENDPOINT_INSTANCE_IFRAME

# specifically for site urls sent to enketo for form retrieval
# `ENKETO_PROTOCOL` variable is overridden when internal domain name is used.
# All internal communications between containers must be HTTP only.
ENKETO_PROTOCOL = os.environ.get('ENKETO_PROTOCOL', 'https')


################################
# MongoDB settings             #
################################

MONGO_DATABASE = {
    'HOST': os.environ.get('KOBOCAT_MONGO_HOST', 'mongo'),
    'PORT': int(os.environ.get('KOBOCAT_MONGO_PORT', 27017)),
    'NAME': os.environ.get('KOBOCAT_MONGO_NAME', 'formhub'),
    'USER': os.environ.get('KOBOCAT_MONGO_USER', ''),
    'PASSWORD': os.environ.get('KOBOCAT_MONGO_PASS', '')
}

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


################################
# Sentry settings              #
################################

if (os.getenv("RAVEN_DSN") or "") != "":
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.celery import CeleryIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration

    # All of this is already happening by default!
    sentry_logging = LoggingIntegration(
        level=logging.INFO,  # Capture info and above as breadcrumbs
        event_level=logging.ERROR  # Send errors as events
    )
    sentry_sdk.init(
        dsn=os.environ['RAVEN_DSN'],
        integrations=[
            DjangoIntegration(),
            CeleryIntegration(),
            sentry_logging
        ],
        send_default_pii=True
    )

# Monkey Patch PyXForm. @ToDo remove after upgrading to v1.1.0
import re

import pyxform.validators.odk_validate
from pyxform.validators.util import (
    run_popen_with_timeout,
)
from pyxform.xform2json import logger

logger.removeHandler(logging.NullHandler)
logger.addHandler(logging.NullHandler())


def patched_check_java_version():
    """
    Monkey patched version of pyxform 0.15.
    pyxform version expected the version to be MAJOR.MINOR.PATCH, but
    newer versions of JAVA can use an extra digit.

    """
    try:
        stderr = str(
            run_popen_with_timeout(
                ["java", "-Djava.awt.headless=true", "-version"], 100
            )[3]
        )
    except OSError as os_error:
        stderr = str(os_error)
    # convert string to unicode for python2
    if sys.version_info.major < 3:
        stderr = stderr.strip().decode("utf-8")
    if "java version" not in stderr and "openjdk version" not in stderr:
        raise EnvironmentError(
            "pyxform odk validate dependency: java not found")
    # extract version number from version string
    java_version_str = stderr.split("\n")[0]
    # version number is usually inside double-quotes.
    # Using regex to find that in the string
    java_version = re.findall(r"\"(.+?)\"", java_version_str)[0]
    parts = java_version.split(".")
    major = parts[0]
    minor = parts[1]
    if not ((int(major) == 1 and int(minor) >= 8) or int(major) >= 8):
        raise EnvironmentError(
            "pyxform odk validate dependency: " "java 8 or newer version not found"
        )


pyxform.validators.odk_validate.check_java_version = patched_check_java_version

