# coding: utf-8
from .base import *

################################
# Django Framework settings    #
################################

# Force `DEBUG` and `TEMPLATE_DEBUG` to `False`
DEBUG = False
TEMPLATES[0]['OPTIONS']['debug'] = False

SESSION_ENGINE = "redis_sessions.session"
# django-redis-session expects a dictionary with `url`
redis_session_url = env.cache_url("REDIS_SESSION_URL", default="redis://redis_cache:6380/2")
SESSION_REDIS = {"url": redis_session_url['LOCATION']}
