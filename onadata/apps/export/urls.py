#################################################
# THIS APP IS DEAD CODE AND SHOULD BE EXCISED   #
# EVERY SINGLE ENDPOINT 500s EXCEPT export_menu #
#################################################

from django.conf.urls import patterns, url


urlpatterns = patterns(
    '',
    url(r"(?P<id_string>[^/]+).csv$",
        'onadata.apps.export.views.csv_export',
        name='formpack_csv_export'),
    url(r"(?P<id_string>[^/]+).xlsx$",
        'onadata.apps.export.views.xlsx_export',
        name='formpack_xlsx_export')
)
