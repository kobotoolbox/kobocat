# coding: utf-8
from __future__ import unicode_literals, print_function, division, absolute_import
import os
import pytest

from django.conf import settings

from onadata.libs.utils.storage import delete_user_storage


@pytest.fixture(scope="session", autouse=True)
def setup(request):
    # Nothing to do at the beginning
    request.addfinalizer(_tear_down)


def _tear_down():
    print("\nCleaning testing environment...")
    print('Removing MongoDB...')
    settings.MONGO_DB.instances.drop()

    root_path = os.path.dirname(os.path.realpath(__file__))
    if os.path.exists(os.path.join(root_path, 'db.sqlite3')):
        print('Removing SQL DB...')
        os.remove(os.path.join(root_path, 'db.sqlite3'))

    test_usernames = [
        'bob',
        'deno'
        'lilly',
        'alice',
        'jo',
        'peter',
        'carl'
    ]
    print("Removing users' storage...")
    for username in test_usernames:
        delete_user_storage(username)
