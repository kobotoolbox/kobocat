# coding: utf-8
from __future__ import unicode_literals, print_function, division, absolute_import
import dj_database_url
from django.utils.six.moves.urllib.parse import quote_plus
from mongomock import MongoClient as MockMongoClient

from onadata.settings.common import *

DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'
TEMPLATE_DEBUG = os.environ.get('TEMPLATE_DEBUG', 'True') == 'True'
TEMPLATE_STRING_IF_INVALID = ''


DATABASES = {
    'default': dj_database_url.config(
        env='TEST_DATABASE_URL', default="sqlite:///%s/db.sqlite3" % BASE_DIR)
}

# Need to add these lines to make the tests run
# Moreover, `apt-get update && apt-get install libsqlite3-mod-spatialite`
#  should be executed inside the container
DATABASES['default']['ENGINE'] = "django.contrib.gis.db.backends.spatialite"
SPATIALITE_LIBRARY_PATH = 'mod_spatialite'


MONGO_CONNECTION_URL = 'mongodb://fakehost/formhub_test'
MONGO_CONNECTION = MockMongoClient(
    MONGO_CONNECTION_URL, j=True, tz_aware=True)
MONGO_DB = MONGO_CONNECTION['formhub_test']


CELERY_BROKER_URL = os.environ.get(
    'KOBOCAT_BROKER_URL', 'amqp://guest:guest@rabbit:5672/')

try:
    SECRET_KEY = os.environ['DJANGO_SECRET_KEY']
except KeyError:
    raise Exception('DJANGO_SECRET_KEY must be set in the environment.')

ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '*').split(' ')

TESTING_MODE = True

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

MEDIA_ROOT = '/tmp/test_media/'
CELERY_TASK_ALWAYS_EAGER = True
BROKER_BACKEND = 'memory'
ENKETO_API_TOKEN = 'abc'

if PRINT_EXCEPTION and DEBUG:
    MIDDLEWARE_CLASSES += ('utils.middleware.ExceptionLoggingMiddleware',)

# include the kobocat-template directory
TEMPLATE_OVERRIDE_ROOT_DIR = os.environ.get(
    'KOBOCAT_TEMPLATES_PATH',
    os.path.abspath(os.path.join(PROJECT_ROOT, 'kobocat-template'))
)
TEMPLATE_DIRS = (os.path.join(TEMPLATE_OVERRIDE_ROOT_DIR, 'templates'),) + TEMPLATE_DIRS
STATICFILES_DIRS += (os.path.join(TEMPLATE_OVERRIDE_ROOT_DIR, 'static'),)

KOBOFORM_SERVER = os.environ.get("KOBOFORM_SERVER", "localhost")
KOBOFORM_SERVER_PORT = os.environ.get("KOBOFORM_SERVER_PORT", "8000")
KOBOFORM_SERVER_PROTOCOL = os.environ.get("KOBOFORM_SERVER_PROTOCOL", "http")
# KOBOFORM_LOGIN_AUTOREDIRECT=True
KOBOFORM_URL = os.environ.get("KOBOFORM_URL", "http://localhost:8000")

TEMPLATE_CONTEXT_PROCESSORS = (
    'onadata.koboform.context_processors.koboform_integration',
) + TEMPLATE_CONTEXT_PROCESSORS

# MIDDLEWARE_CLASSES = ('onadata.koboform.redirect_middleware.ConditionalRedirects', ) + MIDDLEWARE_CLASSES

# Domain must not exclude KPI when sharing sessions
if os.environ.get('SESSION_COOKIE_DOMAIN'):
    SESSION_COOKIE_DOMAIN = os.environ['SESSION_COOKIE_DOMAIN']
    SESSION_COOKIE_NAME = 'kobonaut'

SESSION_SERIALIZER = 'django.contrib.sessions.serializers.JSONSerializer'

# for debugging
# print "KOBOFORM_URL=%s" % KOBOFORM_URL
# print "SECRET_KEY=%s" % SECRET_KEY
# print "CSRF_COOKIE_DOMAIN=%s " % CSRF_COOKIE_DOMAIN

# BEGIN external service integration codes
AWS_ACCESS_KEY_ID = os.environ.get('KOBOCAT_AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('KOBOCAT_AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.environ.get('KOBOCAT_AWS_STORAGE_BUCKET_NAME')
AWS_DEFAULT_ACL = 'private'

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

# Optional Sentry configuration: if desired, be sure to install Raven and set
# RAVEN_DSN in the environment
if 'RAVEN_DSN' in os.environ:
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
        try:
            RAVEN_CONFIG['release'] = raven.fetch_git_sha(BASE_DIR)
        except raven.exceptions.InvalidGitRepository:
            pass

POSTGIS_VERSION = (2, 5, 0)

# DISABLE Django DB logging
LOGGING['loggers']['django.db.backends'] = {
            'level': 'WARNING',
            'propagate': True
        }
