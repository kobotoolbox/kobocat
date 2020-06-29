# coding: utf-8
from __future__ import unicode_literals, print_function, division, absolute_import

import base64

from django.utils.six import string_types


def str2bool(v):
    return v.lower() in (
        'yes', 'true', 't', '1') if isinstance(v, string_types) else v


def base64_encodestring(obj):
    return base64.encodebytes(obj.encode()).decode()


def base64_decodestring(obj):
    if isinstance(obj, str):
        obj = obj.encode()

    return base64.b64decode(obj).decode()
