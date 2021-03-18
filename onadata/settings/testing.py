# coding: utf-8
import os

import dj_database_url
from mongomock import MongoClient as MockMongoClient

from .base import *

################################
# Django Framework settings    #
################################

# By default, PostgreSQL is considered as the default engine. Some DB queries
# rely on PostgreSQL engine to be executed. It needs to be set to `False` to
# make them run with SQLite (i.e. running unit tests locally)
# Database (i.e. PostgreSQL)
DATABASES = {
    'default': dj_database_url.config(
        env='TEST_DATABASE_URL', default="sqlite:///%s/db.sqlite3" % BASE_DIR)
}

if not os.getenv('USE_POSTGRESQL', False):
    # Need to add these lines to make the tests run
    # Moreover, `apt-get update && apt-get install libsqlite3-mod-spatialite`
    #  should be executed inside the container
    DATABASES['default']['ENGINE'] = "django.contrib.gis.db.backends.spatialite"
    SPATIALITE_LIBRARY_PATH = os.environ.get('SPATIALITE_LIBRARY_PATH', 'mod_spatialite')
else:
    DATABASES['default']['ENGINE'] = 'django.contrib.gis.db.backends.postgis'
print('DATABASES', DATABASES, flush=True)

MEDIA_ROOT = '/tmp/test_media/'

# DISABLE Django DB logging
LOGGING['loggers']['django.db.backends'] = {
    'level': 'WARNING',
    'propagate': True
}

SECRET_KEY = os.urandom(50).hex()

###################################
# Django Rest Framework settings  #
###################################


################################
# KoBoCAT settings             #
################################

TESTING_MODE = True
TEST_HTTP_HOST = 'testserver.com'
TEST_USERNAME = 'bob'
USE_POSTGRESQL = os.getenv('USE_POSTGRESQL', False)

################################
# Celery settings              #
################################

CELERY_TASK_ALWAYS_EAGER = True
CELERY_BROKER_TRANSPORT = 'memory'

################################
# Enketo Express settings      #
################################

ENKETO_API_TOKEN = os.urandom(50).hex()

################################
# MongoDB settings             #
################################

MONGO_CONNECTION_URL = 'mongodb://fakehost/formhub_test'
MONGO_CONNECTION = MockMongoClient(
    MONGO_CONNECTION_URL, j=True, tz_aware=True)
MONGO_DB = MONGO_CONNECTION['formhub_test']
