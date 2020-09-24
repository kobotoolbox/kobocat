# coding: utf-8
from __future__ import unicode_literals, print_function, division, absolute_import
import os

from django.conf import settings


def viewer_fixture_path(*args):
    return os.path.join(settings.ONADATA_DIR, 'apps', 'viewer',
                        'tests', 'fixtures', *args)
