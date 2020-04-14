# coding: utf-8
from __future__ import unicode_literals, print_function, division, absolute_import
from onadata import koboform


def koboform_integration(request):
    return {
        u'koboform_url': koboform.url,
        u'koboform_autoredirect': koboform.autoredirect
    }
