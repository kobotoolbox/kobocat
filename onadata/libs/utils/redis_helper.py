# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import re

from django.core.exceptions import ImproperlyConfigured


class RedisHelper(object):
    """
    Redis's helper.

    Mimics dj_database_url

    """

    @staticmethod
    def config(default=None):
        """
        :return: dict
        """

        try:
            redis_connection_url = os.getenv("REDIS_SESSION_URL", default)
            match = re.match(r"redis://(:(?P<password>[^@]*)@)?(?P<host>[^:]+):(?P<port>\d+)(/(?P<index>\d+))?",
                             redis_connection_url)
            if not match:
                # FIXME
                raise Exception()

            redis_connection_dict = {
                "host": match.group("host"),
                "port": match.group("port"),
                "db": match.group("index") or 0,
                "password": match.group("password"),
            }
            return redis_connection_dict

        # FIXME
        except Exception as e:
            raise ImproperlyConfigured(
                "Could not parse Redis URL. Please verify '{}' value".format(
                    env_var
                )
            )


class RedisSessionHelper(RedisHelper):
    # FIXME: reading from the environment should probably happen in
    # `kc_environ.py` or another settings file instead of here
    @classmethod
    def config(cls, default=None):
        redis_connection_dict = super(RedisSessionHelper, cls).config(
            default=default, env_var='REDIS_SESSION_URL'
        )
        redis_connection_dict['prefix'] = os.getenv(
            'REDIS_SESSION_PREFIX', 'session'
        )
        redis_connection_dict['socket_timeout'] = os.getenv(
            'REDIS_SESSION_SOCKET_TIMEOUT', 1
        )
        return redis_connection_dict
