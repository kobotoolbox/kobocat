# coding: utf-8
from __future__ import unicode_literals, print_function, division, absolute_import
from onadata import koboform


def koboform_integration(request):
    return {
        'koboform_url': koboform.url,
        'koboform_autoredirect': koboform.autoredirect
    }
