# this preset is used for automated testing of formhub
#
from common import *  # nopep8

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'onadata_test',
        'USER': 'postgres',
        'PASSWORD': '',
        'HOST': '127.0.0.1',
        # Replacement for TransactionMiddleware
        'ATOMIC_REQUESTS': True,
    }
}

### MONGO ###

MONGO_DATABASE = {
    'HOST': os.environ.get('KOBOCAT_MONGO_HOST', 'localhost'),
    'PORT': int(os.environ.get('KOBOCAT_MONGO_PORT', 27017)),
    'NAME': '__formhub_test_WILL_BE_DESTROYED',
    'USER': os.environ.get('KOBOCAT_MONGO_USER', ''),
    'PASSWORD': os.environ.get('KOBOCAT_MONGO_PASS', '')
}

if MONGO_DATABASE.get('USER') and MONGO_DATABASE.get('PASSWORD'):
    MONGO_CONNECTION_URL = (
        "mongodb://%(USER)s:%(PASSWORD)s@%(HOST)s:%(PORT)s") % MONGO_DATABASE
else:
    MONGO_CONNECTION_URL = "mongodb://%(HOST)s:%(PORT)s" % MONGO_DATABASE

MONGO_CONNECTION = MongoClient(
    MONGO_CONNECTION_URL, safe=True, j=True, tz_aware=True)
MONGO_DB = MONGO_CONNECTION[MONGO_DATABASE['NAME']]

### END MONGO ###

SECRET_KEY = 'mlfs33^s1l4xf6a36$0#j%dd*sisfoi&)&4s-v=91#^l01v)*j'

PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.MD5PasswordHasher',
    'django.contrib.auth.hashers.SHA1PasswordHasher',
)

### JNM TEMPORARY ###
ALLOWED_HOSTS = ('*',)
DEBUG = True
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
#############

if PRINT_EXCEPTION and DEBUG:
    MIDDLEWARE_CLASSES += ('utils.middleware.ExceptionLoggingMiddleware',)

if len(sys.argv) >= 2 and (sys.argv[1] == "test" or sys.argv[1] == "test_all"):
    # This trick works only when we run tests from the command line.
    TESTING_MODE = True
else:
    TESTING_MODE = False

if TESTING_MODE:
    MEDIA_ROOT = os.path.join(ONADATA_DIR, 'test_media/')
    subprocess.call(["rm", "-r", MEDIA_ROOT])
    # need to have CELERY_TASK_ALWAYS_EAGER True and BROKER_BACKEND as memory
    # to run tasks immediately while testing
    CELERY_TASK_ALWAYS_EAGER = True
    BROKER_BACKEND = 'memory'
    ENKETO_API_TOKEN = 'abc'
else:
    MEDIA_ROOT = os.path.join(ONADATA_DIR, 'media/')

# Clear out the test database
if TESTING_MODE:
    MONGO_DB.instances.drop()
