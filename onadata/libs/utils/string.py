# coding: utf-8
import base64
import hashlib

from django.utils.six import string_types


def base64_encodestring(obj):
    return base64.encodebytes(obj.encode()).decode()


def base64_decodestring(obj):
    if isinstance(obj, str):
        obj = obj.encode()

    return base64.b64decode(obj).decode()


def get_hash(hashable, algorithm='md5'):

    supported_algorithm = ['md5', 'sha1']
    if algorithm not in supported_algorithm:
        raise NotImplementedError('Only `{algorithms}` are supported'.format(
            algorithms=', '.join(supported_algorithm)
        ))

    if algorithm == 'md5':
        hashlib_def = hashlib.md5
    else:
        hashlib_def = hashlib.sha1

    if isinstance(hashable, str):
        hashable = hashable.encode()

    return hashlib_def(hashable).hexdigest()


def str2bool(v):
    return v.lower() in (
        'yes', 'true', 't', '1') if isinstance(v, string_types) else v
