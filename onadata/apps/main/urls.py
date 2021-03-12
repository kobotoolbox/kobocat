# coding: utf-8
from django.conf.urls import include, url
from django.conf import settings
from django.contrib import admin
from django.views.generic import RedirectView
from django.views.i18n import JavaScriptCatalog


from onadata.apps.api.urls import router, router_with_patch_list
from onadata.apps.api.urls import XFormListApi
from onadata.apps.api.urls import XFormSubmissionApi
from onadata.apps.api.urls import BriefcaseApi
from onadata.apps.main.service_health import service_health

from onadata.apps.main.views import (
    # main website views
    home,
    login_redirect,
    profile,
    api_token,

    # form specific
    show,
    edit,
    form_photos,
    download_media_data,
    show_form_settings
)

# exporting stuff
from onadata.apps.viewer.views import (
    attachment_url,
    data_export,
    create_export,
    delete_export,
    export_progress,
    export_list,
    export_download,
    kml_export
)
from onadata.apps.logger.views import (
    bulksubmission,
    bulksubmission_form,
    download_xform,
    download_xlsform,
    download_jsonform,
)


# Statistics for superusers. The username is irrelevant, but leave it as
# the first part of the path to avoid collisions
from onadata.apps.logger.views import (
    superuser_stats,
    retrieve_superuser_stats
)

admin.autodiscover()

urlpatterns = [
    # url('') # Same as `url(r'^$', home)`?
    # change Language
    url(r'^i18n/', include('django.conf.urls.i18n')),
    url('^api/v1/', include(router.urls)),
    url('^api/v1/', include(router_with_patch_list.urls)),
    url(r'^service_health/$', service_health),
    url(r'^api-docs/', RedirectView.as_view(url='/api/v1/')),
    url(r'^api/', RedirectView.as_view(url='/api/v1/')),
    url(r'^api/v1', RedirectView.as_view(url='/api/v1/')),

    # django default stuff
    url(r'^accounts/', include('registration.auth_urls')),
    url(r'^admin/', admin.site.urls),
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # oath2_provider
    url(r'^o/', include('oauth2_provider.urls', namespace='oauth2_provider')),

    # main website views
    url(r'^$', home),
    url(r'^forms/(?P<uuid>[^/]+)$', show, name='show_form'),
    url(r'^login_redirect/$', login_redirect),

    # Bring back old url because it's still used by `kpi`
    # ToDo Remove when `kpi#gallery-2` is merged into master
    url(r"^attachment/$", attachment_url, name='attachment_url'),
    url(r"^attachment/(?P<size>[^/]+)$",
        attachment_url, name='attachment_url'),
    url(r"^{}$".format(settings.MEDIA_URL.lstrip('/')), attachment_url, name='attachment_url'),
    url(r"^{}(?P<size>[^/]+)$".format(settings.MEDIA_URL.lstrip('/')),
        attachment_url, name='attachment_url'),
    url(r'^jsi18n/$', JavaScriptCatalog.as_view(),
        {'packages': ('main', 'viewer',)},
        name='javascript-catalog'),
    url(r'^(?P<username>[^/]+)/$',
        profile, name='user_profile'),
    url(r'^(?P<username>[^/]+)/api-token$',
        api_token, name='api_token'),

    # form specific
    url(r'^(?P<username>[^/]+)/forms/(?P<id_string>[^/]+)$',
        show, name='show_form'),
    url(r'^(?P<username>[^/]+)/forms/(?P<id_string>[^/]+)/edit$',
        edit, name='edit_form'),
    url(r'^(?P<username>[^/]+)/forms/(?P<id_string>[^/]+)/photos',
        form_photos, name='form_photos'),
    url(r'^(?P<username>[^/]+)/forms/(?P<id_string>[^/]+)/formid-media/'
        r'(?P<data_id>\d+)', download_media_data, name='download_media_data'),
    url(r'^(?P<username>[^/]+)/forms/(?P<id_string>[^/]+)/form_settings$',
        show_form_settings, name='show_form_settings'),

    # briefcase api urls
    url(r"^(?P<username>\w+)/view/submissionList$",
        BriefcaseApi.as_view({'get': 'list', 'head': 'list'}),
        name='view-submission-list'),
    url(r"^(?P<username>\w+)/view/downloadSubmission$",
        BriefcaseApi.as_view({'get': 'retrieve', 'head': 'retrieve'}),
        name='view-download-submission'),
    url(r"^(?P<username>\w+)/formUpload$",
        BriefcaseApi.as_view({'post': 'create', 'head': 'create'}),
        name='form-upload'),
    url(r"^(?P<username>\w+)/upload$",
        BriefcaseApi.as_view({'post': 'create', 'head': 'create'}),
        name='upload'),

    # exporting stuff
    url(r"^(?P<username>\w+)/forms/(?P<id_string>[^/]+)/data\.csv$",
        data_export, name='csv_export',
        kwargs={'export_type': 'csv'}),
    url(r"^(?P<username>\w+)/forms/(?P<id_string>[^/]+)/data\.xls",
        data_export, name='xls_export',
        kwargs={'export_type': 'xls'}),
    url(r"^(?P<username>\w+)/forms/(?P<id_string>[^/]+)/data\.kml$",
        kml_export),
    url(r"^(?P<username>\w+)/exports/(?P<id_string>[^/]+)/(?P<export_type>\w+)"
        r"/new$", create_export, name='create_export'),
    url(r"^(?P<username>\w+)/exports/(?P<id_string>[^/]+)/(?P<export_type>\w+)"
        r"/delete$", delete_export, name='delete_export'),
    url(r"^(?P<username>\w+)/exports/(?P<id_string>[^/]+)/(?P<export_type>\w+)"
        r"/progress$", export_progress, name='export_progress'),
    url(r"^(?P<username>\w+)/exports/(?P<id_string>[^/]+)/(?P<export_type>\w+)"
        r"/$", export_list, name='export_list'),
    url(r"^(?P<username>\w+)/exports/(?P<id_string>[^/]+)/(?P<export_type>\w+)"
        "/(?P<filename>[^/]+)$",
        export_download, name='export_download'),

    # odk data urls
    url(r"^submission$",
        XFormSubmissionApi.as_view({'post': 'create', 'head': 'create'}),
        name='submissions'),
    url(r"^formList$",
        XFormListApi.as_view({'get': 'list'}), name='form-list'),
    url(r"^(?P<username>\w+)/formList$",
        XFormListApi.as_view({'get': 'list'}), name='form-list'),
    url(r"^(?P<username>\w+)/xformsManifest/(?P<pk>[\d+^/]+)$",
        XFormListApi.as_view({'get': 'manifest'}),
        name='manifest-url'),
    url(r"^xformsManifest/(?P<pk>[\d+^/]+)$",
        XFormListApi.as_view({'get': 'manifest'}),
        name='manifest-url'),
    url(r"^(?P<username>\w+)/xformsMedia/(?P<pk>[\d+^/]+)"
        r"/(?P<metadata>[\d+^/.]+)$",
        XFormListApi.as_view({'get': 'media'}), name='xform-media'),
    url(r"^(?P<username>\w+)/xformsMedia/(?P<pk>[\d+^/]+)"
        r"/(?P<metadata>[\d+^/.]+)\.(?P<format>[a-z0-9]+)$",
        XFormListApi.as_view({'get': 'media'}), name='xform-media'),
    url(r"^xformsMedia/(?P<pk>[\d+^/]+)/(?P<metadata>[\d+^/.]+)$",
        XFormListApi.as_view({'get': 'media'}), name='xform-media'),
    url(r"^xformsMedia/(?P<pk>[\d+^/]+)/(?P<metadata>[\d+^/.]+)\."
        r"(?P<format>[a-z0-9]+)$",
        XFormListApi.as_view({'get': 'media'}), name='xform-media'),
    url(r"^(?P<username>\w+)/submission$",
        XFormSubmissionApi.as_view({'post': 'create', 'head': 'create'}),
        name='submissions'),
    url(r"^(?P<username>\w+)/bulk-submission$",
        bulksubmission),
    url(r"^(?P<username>\w+)/bulk-submission-form$",
        bulksubmission_form),
    url(r"^(?P<username>\w+)/forms/(?P<pk>[\d+^/]+)/form\.xml$",
        XFormListApi.as_view({'get': 'retrieve'}),
        name="download_xform"),
    url(r"^(?P<username>\w+)/forms/(?P<id_string>[^/]+)/form\.xml$",
        download_xform, name="download_xform"),
    url(r"^(?P<username>\w+)/forms/(?P<id_string>[^/]+)/form\.xls$",
        download_xlsform,
        name="download_xlsform"),
    url(r"^(?P<username>\w+)/forms/(?P<id_string>[^/]+)/form\.json",
        download_jsonform,
        name="download_jsonform"),
    url(r'^favicon\.ico',
        RedirectView.as_view(url='/static/images/favicon.ico')),

    # Statistics for superusers. The username is irrelevant, but leave it as
    # the first part of the path to avoid collisions
    url(r"^(?P<username>[^/]+)/superuser_stats/$",
        superuser_stats),
    url(r"^(?P<username>[^/]+)/superuser_stats/(?P<base_filename>[^/]+)$",
        retrieve_superuser_stats),
]
