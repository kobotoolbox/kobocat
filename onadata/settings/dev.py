# coding: utf-8
from .prod import *


LOGGING['handlers']['console'] = {
    'level': 'DEBUG',
    'class': 'logging.StreamHandler',
    'formatter': 'verbose'
}

#sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)
