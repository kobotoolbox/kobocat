from django.core.cache import caches
from django.test import TestCase
from .cache import RedisCacheNonceStorage


class TestCacheNonceStorage(TestCase):
    def setUp(self):
        self.test_user = 'user'
        self.cache = caches['default']
        self.storage = RedisCacheNonceStorage()

    def test_store_and_update(self):
        self.storage.store_nonce(self.test_user, 'abc', '')
        self.assertEqual(self.cache.get(f'user_nonce_{self.test_user}_abc'), '')

        # Should return true if the user + nonce already exists
        self.assertTrue(self.storage.update_existing_nonce(self.test_user, 'abc', None))

        self.assertFalse(self.storage.update_existing_nonce(self.test_user, 'ab', None))
        self.assertFalse(self.storage.update_existing_nonce('someone', 'abc', None))

        self.cache.clear()
        self.assertFalse(self.storage.update_existing_nonce(self.test_user, 'abc', None))
        # update should never create
        self.assertFalse(self.storage.update_existing_nonce(self.test_user, 'abc', None))

    def test_update_count(self):
        self.storage.store_nonce(self.test_user, 'abc', 2)

        self.assertFalse(self.storage.update_existing_nonce(self.test_user, 'abc', 2))
        self.assertTrue(self.storage.update_existing_nonce(self.test_user, 'abc', 3))
    
    def xtest_nonce_lock(self):
        """
        Prove the lock halts execution, intended to be manually run
        """
        nonce = 'abc'
        self.storage.store_nonce(self.test_user, nonce, 1)
        with self.cache.lock(f'user_nonce_lock_{self.test_user}_{nonce}'):
            self.storage.update_existing_nonce(self.test_user, nonce, 2)
        self.assertTrue()
