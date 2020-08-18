# coding: utf-8
from __future__ import unicode_literals, print_function, division, absolute_import
#################################################
# THIS APP IS DEAD CODE AND SHOULD BE EXCISED   #
# EVERY SINGLE ENDPOINT 500s EXCEPT export_menu #
#################################################

from django.conf.urls import patterns, url


urlpatterns = patterns(
    '',
    url(r"(?P<id_string>[^/]+)/$",
        'onadata.apps.export.views.export_menu',
        name='formpack_export_menu'),
    url(r"(?P<id_string>[^/]+).csv$",
        'onadata.apps.export.views.csv_export',
        name='formpack_csv_export'),
    url(r"(?P<id_string>[^/]+).xlsx$",
        'onadata.apps.export.views.xlsx_export',
        name='formpack_xlsx_export'),
    url(r"(?P<id_string>[^/]+).html$",
        'onadata.apps.export.views.html_export',
        name='formpack_html_export')
)
