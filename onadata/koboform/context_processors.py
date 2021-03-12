# coding: utf-8
from onadata import koboform


def koboform_integration(request):
    return {
        'koboform_url': koboform.url,
        'koboform_autoredirect': koboform.autoredirect
    }
