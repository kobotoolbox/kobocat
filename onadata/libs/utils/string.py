# coding: utf-8
from __future__ import unicode_literals, print_function, division, absolute_import

from django.utils.six import string_types


def str2bool(v):
    return v.lower() in (
        'yes', 'true', 't', '1') if isinstance(v, string_types) else v
