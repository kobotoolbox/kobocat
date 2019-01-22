# -*- coding: utf-8 -*-
from __future__ import absolute_import
import sys
from .kc_environ import *


LOGGING['handlers']['console'] = {
    'level': 'DEBUG',
    'class': 'logging.StreamHandler',
    'formatter': 'verbose'
}

LOGGING['loggers']['werkzeug'] = {
    'handlers': ['console'],
    'level': 'DEBUG',
    'propagate': True,
}
