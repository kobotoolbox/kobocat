# coding: utf-8
import dj_database_url
from mongomock import MongoClient as MockMongoClient

from .base import *

DATABASES = {
    'default': dj_database_url.config(
        env='TEST_DATABASE_URL', default="sqlite:///%s/db.sqlite3" % BASE_DIR)
}

# Need to add these lines to make the tests run
# Moreover, `apt-get update && apt-get install libsqlite3-mod-spatialite`
#  should be executed inside the container
DATABASES['default']['ENGINE'] = "django.contrib.gis.db.backends.spatialite"
SPATIALITE_LIBRARY_PATH = os.environ.get('SPATIALITE_LIBRARY_PATH', 'mod_spatialite')


MONGO_CONNECTION_URL = 'mongodb://fakehost/formhub_test'
MONGO_CONNECTION = MockMongoClient(
    MONGO_CONNECTION_URL, j=True, tz_aware=True)
MONGO_DB = MONGO_CONNECTION['formhub_test']

TESTING_MODE = True

MEDIA_ROOT = '/tmp/test_media/'
CELERY_TASK_ALWAYS_EAGER = True
BROKER_BACKEND = 'memory'
ENKETO_API_TOKEN = 'abc'

# DISABLE Django DB logging
LOGGING['loggers']['django.db.backends'] = {
            'level': 'WARNING',
            'propagate': True
        }

GUARDIAN_GET_INIT_ANONYMOUS_USER = 'onadata.apps.main.models.user_profile.get_anonymous_user_instance'

# fake endpoints for testing
TEST_HTTP_HOST = 'testserver.com'
TEST_USERNAME = 'bob'
