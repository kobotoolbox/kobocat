# coding: utf-8
from .prod import *

LOGGING['handlers']['console'] = {
    'level': 'DEBUG',
    'class': 'logging.StreamHandler',
    'formatter': 'verbose',
    'stream': sys.stdout,
}
LOGGING['root'] = {
    'handlers': ['console'],
    'level': 'DEBUG'
}

MIDDLEWARE.append('onadata.libs.utils.middleware.ExceptionLoggingMiddleware')
