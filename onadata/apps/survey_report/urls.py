# coding: utf-8
from __future__ import unicode_literals, print_function, division, absolute_import

from django.conf.urls import url
from onadata.apps.survey_report.views import (
    export_menu,
    csv_export,
    xlsx_export,
    html_export,
    view_one_submission,
    autoreport_menu,
    auto_report
)

urlpatterns = [
    # url('', name='formpack_home'),
    url(r"(?P<id_string>[^/]+)/export/$",
        export_menu,
        name='formpack_export_menu'),

    url(r"(?P<id_string>[^/]+)/export.csv$",
        csv_export,
        name='formpack_csv_export'),
    url(r"(?P<id_string>[^/]+)/export.xlsx$",
        xlsx_export,
        name='formpack_xlsx_export'),
    url(r"(?P<id_string>[^/]+)/export.html$",
        html_export,
        name='formpack_html_export'),

    url(r"(?P<id_string>[^/]+)/submission/(?P<submission>\d+).html$",
        view_one_submission,
        name='formpack_one_submission'),

    url(r"(?P<id_string>[^/]+)/digest/$",
        autoreport_menu,
        name='formpack_autoreport_menu'),
    url(r"(?P<id_string>[^/]+)/digest.html$",
        auto_report,
        name='formpack_auto_report')
]
