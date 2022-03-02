# coding: utf-8
from .base import *

################################
# Django Framework settings    #
################################

# Force `DEBUG` and `TEMPLATE_DEBUG` to `False`
DEBUG = False
TEMPLATES[0]['OPTIONS']['debug'] = False

SESSION_ENGINE = "redis_sessions.session"
SESSION_REDIS = env.cache_url("REDIS_SESSION_URL", default="redis://redis_cache:6380/2")
