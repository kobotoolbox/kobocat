# coding: utf-8
from django.urls import re_path

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
    # re_path('', name='formpack_home'),
    re_path(r"(?P<id_string>[^/]+)/export/$",
            export_menu,
            name='formpack_export_menu'),

    re_path(r"(?P<id_string>[^/]+)/export.csv$",
            csv_export,
            name='formpack_csv_export'),
    re_path(r"(?P<id_string>[^/]+)/export.xlsx$",
            xlsx_export,
            name='formpack_xlsx_export'),
    re_path(r"(?P<id_string>[^/]+)/export.html$",
            html_export,
            name='formpack_html_export'),

    re_path(r"(?P<id_string>[^/]+)/submission/(?P<submission>\d+).html$",
            view_one_submission,
            name='formpack_one_submission'),

    re_path(r"(?P<id_string>[^/]+)/digest/$",
            autoreport_menu,
            name='formpack_autoreport_menu'),
    re_path(r"(?P<id_string>[^/]+)/digest.html$",
            auto_report,
            name='formpack_auto_report')
]
