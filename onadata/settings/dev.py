# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function
import functools
import sys

from .kc_environ import *


LOGGING['handlers']['console'] = {
    'level': 'DEBUG',
    'class': 'logging.StreamHandler',
    'formatter': 'verbose'
}

sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)
