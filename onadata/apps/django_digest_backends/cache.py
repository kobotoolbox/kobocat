from django.core.cache import caches
from django_digest.utils import get_setting


DIGEST_NONCE_CACHE_NAME = get_setting('DIGEST_NONCE_CACHE_NAME', 'default')
NONCE_TIMEOUT = get_setting('DIGEST_NONCE_TIMEOUT_IN_SECONDS', 5 * 60)
NONCE_NO_COUNT = ''  # Needs to be something other than None to determine not set vs set to null


class RedisCacheNonceStorage():
    def _get_cache(self):
        # Dynamic fetching of cache is necessary to work with override_settings
        return caches[DIGEST_NONCE_CACHE_NAME]

    def _generate_cache_key(self, user, nonce):
        return f'user_nonce_{user}_{nonce}'

    def update_existing_nonce(self, user, nonce, nonce_count):
        """
        Check and update nonce record. If no record exists or has an invalid count,
        return False. Create a lock to prevent a concurrent replay attack where
        two requests are send immediately and either may finish first.
        """
        cache = self._get_cache()
        cache_key = self._generate_cache_key(user, nonce)

        if nonce_count == None:  # No need to lock
            existing = cache.get(cache_key)
            if existing is None:
                return False
            cache.set(cache_key, NONCE_NO_COUNT, NONCE_TIMEOUT)
        else:
            with cache.lock(
                f'user_nonce_lock_{user}_{nonce}',
                timeout=NONCE_TIMEOUT,
                blocking_timeout=30
            ):
                existing = cache.get(cache_key)
                if existing is None:
                    return False
                if nonce_count <= existing:
                    return False
                cache.set(cache_key, nonce_count, NONCE_TIMEOUT)
        return True

    def store_nonce(self, user, nonce, nonce_count):
        # Nonce is required
        if nonce is None or len(nonce) <= 1:
            return False
        if nonce_count is None:
            nonce_count = NONCE_NO_COUNT
        cache = self._get_cache()
        cache_key = self._generate_cache_key(user, nonce)
        return cache.set(cache_key, nonce_count, NONCE_TIMEOUT)
