# coding: utf-8
from contextlib import contextmanager
from .base import *

DATABASES = {
    'default': env.db_url('KC_DATABASE_URL'),
    'default_destination': env.db_url('KC_DATABASE_URL_DESTINATION'),
}
DATABASES['default']['OPTIONS'] = {
    'options': '-c default_transaction_read_only=on'
}

# Mongo stuff just copied from base.py
MONGO_DB_URL = env.str('MONGO_DB_URL_DESTINATION')
# Attempt to get collection name from the connection string
# fallback on MONGO_DB_NAME or 'formhub' if it is empty or None or unable to parse
try:
    mongo_db_name = env.db_url('MONGO_DB_URL_DESTINATION').get(
        'NAME'
    ) or env.str('MONGO_DB_NAME', 'formhub')
except ValueError:  # db_url is unable to parse replica set strings
    mongo_db_name = env.str('MONGO_DB_NAME', 'formhub')

mongo_client = MongoClient(
    MONGO_DB_URL, connect=False, journal=True, tz_aware=True
)
MONGO_DB = mongo_client[mongo_db_name]


class HitTheRoadDatabaseRouter:
    _use_dest_db = False

    @classmethod
    @contextmanager
    def route_to_destination(cls):
        cls._use_dest_db = True
        yield
        cls._use_dest_db = False

    @classmethod
    def db_for_whatever(cls):
        if cls._use_dest_db:
            # print('orm → dest db', flush=True)
            return 'default_destination'
        # print('orm → source db', flush=True)
        return 'default'

    @classmethod
    def db_for_read(cls, *args, **kwargs):
        return cls.db_for_whatever()

    @classmethod
    def db_for_write(cls, *args, **kwargs):
        return cls.db_for_whatever()

    @staticmethod
    def allow_relation(*args, **kwargs):
        return True

    @staticmethod
    def allow_migrate(*args, **kwargs):
        return False


DATABASE_ROUTERS = [HitTheRoadDatabaseRouter]
