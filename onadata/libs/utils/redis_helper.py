# coding: utf-8
from __future__ import unicode_literals, print_function, division, absolute_import
import os
import re

from django.utils.six.moves.urllib.parse import unquote_plus


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
            redis_connection_url = os.getenv('REDIS_SESSION_URL', default)
            match = re.match(r'redis://(:(?P<password>[^@]*)@)?(?P<host>[^:]+):(?P<port>\d+)(/(?P<index>\d+))?',
                             redis_connection_url)
            if not match:
                raise Exception()

            if match.group('password') is None:
                password = None
            else:
                password = unquote_plus(match.group('password'))

            redis_connection_dict = {
                'host': match.group('host'),
                'port': match.group('port'),
                'db': match.group('index') or 0,
                'password': password,
                'prefix': os.getenv('REDIS_SESSION_PREFIX', 'session'),
                'socket_timeout': os.getenv('REDIS_SESSION_SOCKET_TIMEOUT', 1),
            }

            return redis_connection_dict
        except Exception as e:
            raise Exception("Could not parse Redis session URL. Please verify 'REDIS_SESSION_URL' value")
