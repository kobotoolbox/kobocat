# coding: utf-8
from onadata.libs.utils.redis_helper import RedisHelper
from .base import *

################################
# Django Framework settings    #
################################

LOGGING['root'] = {
    'handlers': ['console'],
    'level': 'DEBUG'
}

SESSION_ENGINE = "redis_sessions.session"
SESSION_REDIS = RedisHelper.config(default="redis://redis_cache:6380/2")
