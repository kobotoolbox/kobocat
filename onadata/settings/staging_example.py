from common import *  # nopep8

DEBUG = True
TEMPLATE_DEBUG = DEBUG
TEMPLATE_STRING_IF_INVALID = ''

# see: http://docs.djangoproject.com/en/dev/ref/settings/#databases

# postgres
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'formhub_dev',
        'USER': 'formhub_dev',
        'PASSWORD': '12345678',
        'HOST': 'localhost',
        # Replacement for TransactionMiddleware
        'ATOMIC_REQUESTS': True,
    },
}

# TIME_ZONE = 'UTC'

TOUCHFORMS_URL = 'http://localhost:9000/'

SECRET_KEY = 'mlfs33^s1l4xf6a36$0#srgcpj%dd*sisfo6HOktYXB9y'

TESTING_MODE = False
if len(sys.argv) >= 2 and (sys.argv[1] == "test" or sys.argv[1] == "test_all"):
    # This trick works only when we run tests from the command line.
    TESTING_MODE = True
else:
    TESTING_MODE = False

if TESTING_MODE:
    MEDIA_ROOT = os.path.join(ONADATA_DIR, 'test_media/')
    subprocess.call(["rm", "-r", MEDIA_ROOT])
    MONGO_DATABASE['NAME'] = "formhub_test"
    # need to have CELERY_TASK_ALWAYS_EAGER True and BROKER_BACKEND as memory
    # to run tasks immediately while testing
    CELERY_TASK_ALWAYS_EAGER = True
    BROKER_BACKEND = 'memory'
    ENKETO_API_TOKEN = 'abc'
else:
    MEDIA_ROOT = os.path.join(ONADATA_DIR, 'media/')

if PRINT_EXCEPTION and DEBUG:
    MIDDLEWARE_CLASSES += ('utils.middleware.ExceptionLoggingMiddleware',)
# Clear out the test database
if TESTING_MODE:
    MONGO_DB.instances.drop()
