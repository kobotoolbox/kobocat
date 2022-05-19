# coding: utf-8
import time

from django.conf import settings
from django.http import HttpResponse
from redis import Redis

from onadata.apps.logger.models import Instance


def service_health(request):
    """
    Return a HTTP 200 if some very basic runtime tests of the application
    pass. Otherwise, return HTTP 500
    """
    any_failure = False

    t0 = time.time()
    try:
        settings.MONGO_DB.instances.find_one()
    except Exception as e:
        mongo_message = repr(e)
        any_failure = True
    else:
        mongo_message = 'OK'
    mongo_time = time.time() - t0

    t0 = time.time()
    try:
        Instance.objects.first()
    except Exception as e:
        postgres_message = repr(e)
        any_failure = True
    else:
        postgres_message = 'OK'
    postgres_time = time.time() - t0

    t0 = time.time()
    try:
        rset = settings.SESSION_REDIS
        success = Redis(socket_timeout=1).from_url(rset['url']).ping()
        any_failure = not success
        redis_cache_message = 'OK'
    except Exception as e:
        any_failure = True
        redis_cache_message = repr(e)
    redis_cache_time = time.time() - t0

    t0 = time.time()
    try:
        redis_main_url = settings.CELERY_BROKER_URL
        success = Redis(socket_timeout=1).from_url(redis_main_url).ping()
        any_failure = not success
        redis_main_message = 'OK'
    except Exception as e:
        any_failure = True
        redis_main_message = repr(e)
    redis_main_time = time.time() - t0

    output = (
        '{}\r\n\r\n'
        'Mongo: {} in {:.3} seconds\r\n'
        'Postgres: {} in {:.3} seconds\r\n'
        'Redis Cache {} in {:.3} seconds\r\n'
        'Redis Main {} in {:.3} seconds\r\n'
    ).format(
        'FAIL' if any_failure else 'OK',
        mongo_message, mongo_time,
        postgres_message, postgres_time,
        redis_cache_message, redis_cache_time,
        redis_main_message, redis_main_time
    )

    return HttpResponse(
        output, status=(500 if any_failure else 200), content_type='text/plain'
    )

