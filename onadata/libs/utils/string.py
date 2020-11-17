# coding: utf-8
from __future__ import unicode_literals, print_function, division, absolute_import
def str2bool(v):
    return v.lower() in (
        'yes', 'true', 't', '1') if isinstance(v, basestring) else v
