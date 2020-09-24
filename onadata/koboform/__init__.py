# coding: utf-8
from __future__ import unicode_literals, print_function, division, absolute_import
from django.conf import settings


url = False
if hasattr(settings, 'KOBOFORM_URL') and settings.KOBOFORM_URL:
    url = settings.KOBOFORM_URL
else:
    url = False

active = bool(url)

autoredirect = active
if active and hasattr(settings, 'KOBOFORM_LOGIN_AUTOREDIRECT'):
    autoredirect = settings.KOBOFORM_LOGIN_AUTOREDIRECT


def redirect_url(url_param):
    if url:
        return url + url_param


def login_url(next_kobocat_url=False, next_url=False):
    # use kpi login if configuration exists
    if settings.KPI_URL:
        url = settings.KPI_URL

        if url:
            url_param = url + '/accounts/login/'
            if next_kobocat_url:
                next_url = '/kobocat%s' % next_kobocat_url
            if next_url:
                url_param += "?next=%s" % next_url
            return url_param
