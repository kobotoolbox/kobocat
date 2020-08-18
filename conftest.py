# coding: utf-8
from __future__ import unicode_literals, print_function, division, absolute_import
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

try:
    INTERRUPTED = pytest.ExitCode.INTERRUPTED  # pytest 5
except AttributeError:
    INTERRUPTED = 2


def stderr_prompt(message):
    sys.stderr.write(message)
    # FIXME: Python 3 compatibility
    return raw_input().strip()


def toggle_capturing(capture_manager, stop):
    if stop:
        capture_manager.suspend_global_capture()
        capture_manager.stop_global_capturing()
    else:
        capture_manager.start_global_capturing()
        capture_manager.resume_global_capture()


@pytest.fixture(scope="session", autouse=True)
def setup(request):
    # We need to disable global capturing in case `-s` is not passed to `pytest`
    # by the users to force print the safeguard messages about data loss.
    capture_manager = request.config.pluginmanager.getplugin("capturemanager")
    is_global_capturing = capture_manager.is_globally_capturing()

    if is_global_capturing:
        toggle_capturing(capture_manager, stop=True)

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
                if is_global_capturing:
                    toggle_capturing(capture_manager, stop=False)
                pytest.exit('User interrupted tests', INTERRUPTED)

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
            if is_global_capturing:
                toggle_capturing(capture_manager, stop=False)
            pytest.exit('User interrupted tests', INTERRUPTED)

    if is_global_capturing:
        toggle_capturing(capture_manager, stop=False)

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
