# coding: utf-8
import os
import pytest
import sys

from django.conf import settings

from onadata.libs.utils.storage import delete_user_storage, user_storage_exists

TEST_USERNAMES = [
    'alice',
    'auser',
    'bob',
    'carl',
    'deno'
    'harry',
    'jo',
    'lilly',
    'peter',
]


def stderr_prompt(message):
    sys.stderr.write(message)
    # FIXME: Python 3 compatibility
    return raw_input().strip()


@pytest.fixture(scope="session", autouse=True)
def setup(request):

    for username in TEST_USERNAMES:
        if user_storage_exists(username):
            response = stderr_prompt(
                '\n\n'
                'WARNING - DATA LOSS! A storage directory already exists for '
                'user {}, but it will be DELETED if you continue with these '
                'tests!\nPlease type "yes" to proceed anyway, or "no" to '
                'cancel: '.format(username)
            )
            if response.lower() != 'yes':
                sys.exit(1)

    if 'instances' in settings.MONGO_DB.collection_names():
        response = stderr_prompt(
            '\n\n'
            'WARNING: the MongoDB collection {}.instances already exists!\n'
            "Type 'yes' if you would like to delete it, or 'no' to "
            'cancel: '.format(settings.MONGO_DB.name)
        )
        if response.lower() == 'yes':
            settings.MONGO_DB.instances.drop()
        else:
            sys.exit(1)

    request.addfinalizer(_tear_down)


def _tear_down():
    print("\nCleaning testing environment...")
    print('Removing MongoDB...')
    settings.MONGO_DB.instances.drop()

    root_path = os.path.dirname(os.path.realpath(__file__))
    if os.path.exists(os.path.join(root_path, 'db.sqlite3')):
        print('Removing SQL DB...')
        os.remove(os.path.join(root_path, 'db.sqlite3'))

    print("Removing users' storage...")
    for username in TEST_USERNAMES:
        delete_user_storage(username)
