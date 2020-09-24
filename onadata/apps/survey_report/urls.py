# coding: utf-8
from __future__ import unicode_literals, print_function, division, absolute_import
from django.conf.urls import patterns, url


urlpatterns = patterns(
    '',
    url(r"(?P<id_string>[^/]+)/export/$",
        'onadata.apps.survey_report.views.export_menu',
        name='formpack_export_menu'),

    url(r"(?P<id_string>[^/]+)/export.csv$",
        'onadata.apps.survey_report.views.csv_export',
        name='formpack_csv_export'),
    url(r"(?P<id_string>[^/]+)/export.xlsx$",
        'onadata.apps.survey_report.views.xlsx_export',
        name='formpack_xlsx_export'),
    url(r"(?P<id_string>[^/]+)/export.html$",
        'onadata.apps.survey_report.views.html_export',
        name='formpack_html_export'),

    url(r"(?P<id_string>[^/]+)/submission/(?P<submission>\d+).html$",
        'onadata.apps.survey_report.views.view_one_submission',
        name='formpack_one_submission'),

    url(r"(?P<id_string>[^/]+)/digest/$",
        'onadata.apps.survey_report.views.autoreport_menu',
        name='formpack_autoreport_menu'),
    url(r"(?P<id_string>[^/]+)/digest.html$",
        'onadata.apps.survey_report.views.auto_report',
        name='formpack_auto_report')
)
