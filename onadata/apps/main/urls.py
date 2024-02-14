# coding: utf-8
from django.conf import settings
from django.contrib import admin

from django.urls import include, re_path, path
from django.views.generic import RedirectView
from django.views.i18n import JavaScriptCatalog

from onadata import koboform
from onadata.apps.api.urls import BriefcaseApi
from onadata.apps.api.urls import XFormListApi
from onadata.apps.api.urls import XFormSubmissionApi
from onadata.apps.api.urls import router, router_with_patch_list
from onadata.apps.main.service_health import service_health, service_health_minimal

# exporting stuff
from onadata.apps.viewer.views import (
    attachment_url,
    create_export,
    delete_export,
    export_progress,
    export_list,
    export_download,
)
from onadata.apps.logger.views import (
    bulksubmission,
    bulksubmission_form,
    download_xlsform,
    download_jsonform,
)

admin.autodiscover()

urlpatterns = [
    # change Language
    re_path(r'^i18n/', include('django.conf.urls.i18n')),
    re_path('^api/v1/', include(router.urls)),
    re_path('^api/v1/', include(router_with_patch_list.urls)),
    re_path(r'^service_health/$', service_health),
    path(r'^service_health/minimal/$', service_health_minimal, name='service-health-minimal'),
    re_path(r'^api/', RedirectView.as_view(url='/api/v1/')),
    re_path(r'^api/v1', RedirectView.as_view(url='/api/v1/')),

    # django default stuff
    re_path(r'^accounts/', include('django.contrib.auth.urls')),
    re_path(r'^admin/', admin.site.urls),

    # oath2_provider
    re_path(r'^o/', include('oauth2_provider.urls', namespace='oauth2_provider')),

    # main website views
    re_path(
        r'^$', RedirectView.as_view(url=koboform.redirect_url('/')), name='home'
    ),
    # Bring back old url because it's still used by `kpi`
    re_path(r"^attachment/$", attachment_url, name='attachment_url'),
    re_path(r"^attachment/(?P<size>[^/]+)$",
            attachment_url, name='attachment_url'),
    re_path(r"^{}$".format(settings.MEDIA_URL.lstrip('/')), attachment_url, name='attachment_url'),
    re_path(r"^{}(?P<size>[^/]+)$".format(settings.MEDIA_URL.lstrip('/')),
            attachment_url, name='attachment_url'),
    re_path(r'^jsi18n/$', JavaScriptCatalog.as_view(packages=['onadata.apps.main', 'onadata.apps.viewer']),
            name='javascript-catalog'),
    re_path(
        r'^(?P<username>[^/]+)/$',
        RedirectView.as_view(url=koboform.redirect_url('/')),
        name='user_profile',
    ),

    # briefcase api urls
    re_path(r"^view/submissionList$",
            BriefcaseApi.as_view({'get': 'list', 'head': 'list'}),
            name='view-submission-list'),
    re_path(r"^view/downloadSubmission$",
            BriefcaseApi.as_view({'get': 'retrieve', 'head': 'retrieve'}),
            name='view-download-submission'),
    re_path(r"^formUpload$",
            BriefcaseApi.as_view({'post': 'create', 'head': 'create'}),
            name='form-upload'),
    re_path(r"^upload$",
            BriefcaseApi.as_view({'post': 'create', 'head': 'create'}),
            name='upload'),

    # exporting stuff
    re_path(r"^(?P<username>\w+)/exports/(?P<id_string>[^/]+)/(?P<export_type>\w+)"
            r"/new$", create_export, name='create_export'),
    re_path(r"^(?P<username>\w+)/exports/(?P<id_string>[^/]+)/(?P<export_type>\w+)"
            r"/delete$", delete_export, name='delete_export'),
    re_path(r"^(?P<username>\w+)/exports/(?P<id_string>[^/]+)/(?P<export_type>\w+)"
            r"/progress$", export_progress, name='export_progress'),
    re_path(r"^(?P<username>\w+)/exports/(?P<id_string>[^/]+)/(?P<export_type>\w+)"
            r"/$", export_list, name='export_list'),
    re_path(r"^(?P<username>\w+)/exports/(?P<id_string>[^/]+)/(?P<export_type>\w+)"
            "/(?P<filename>[^/]+)$",
            export_download, name='export_download'),

    # odk data urls
    re_path(r"^submission$",
            XFormSubmissionApi.as_view({'post': 'create', 'head': 'create'}),
            name='submissions'),
    re_path(r"^formList$",
            XFormListApi.as_view({'get': 'list'}), name='form-list'),
    re_path(r"^(?P<username>\w+)/formList$",
            XFormListApi.as_view({'get': 'list'}), name='form-list'),
    re_path(r"^(?P<username>\w+)/xformsManifest/(?P<pk>[\d+^/]+)$",
            XFormListApi.as_view({'get': 'manifest'}),
            name='manifest-url'),
    re_path(r"^xformsManifest/(?P<pk>[\d+^/]+)$",
            XFormListApi.as_view({'get': 'manifest'}),
            name='manifest-url'),
    re_path(r"^(?P<username>\w+)/xformsMedia/(?P<pk>[\d+^/]+)"
            r"/(?P<metadata>[\d+^/.]+)$",
            XFormListApi.as_view({'get': 'media'}), name='xform-media'),
    re_path(r"^(?P<username>\w+)/xformsMedia/(?P<pk>[\d+^/]+)"
            r"/(?P<metadata>[\d+^/.]+)\.(?P<format>[a-z0-9]+)$",
            XFormListApi.as_view({'get': 'media'}), name='xform-media'),
    re_path(r"^xformsMedia/(?P<pk>[\d+^/]+)/(?P<metadata>[\d+^/.]+)$",
            XFormListApi.as_view({'get': 'media'}), name='xform-media'),
    re_path(r"^xformsMedia/(?P<pk>[\d+^/]+)/(?P<metadata>[\d+^/.]+)\."
            r"(?P<format>[a-z0-9]+)$",
            XFormListApi.as_view({'get': 'media'}), name='xform-media'),
    re_path(r"^(?P<username>\w+)/submission$",
            XFormSubmissionApi.as_view({'post': 'create', 'head': 'create'}),
            name='submissions'),
    re_path(r"^(?P<username>\w+)/bulk-submission$",
            bulksubmission),
    re_path(r"^(?P<username>\w+)/bulk-submission-form$",
            bulksubmission_form),
    re_path(r'^forms/(?P<pk>[\d+^/]+)/form\.xml$',
            XFormListApi.as_view({'get': 'retrieve'}),
            name='download_xform'),
    re_path(r'^(?P<username>\w+)/forms/(?P<pk>[\d+^/]+)/form\.xml$',
            XFormListApi.as_view({'get': 'retrieve'}),
            name='download_xform'),
    re_path(r"^(?P<username>\w+)/forms/(?P<id_string>[^/]+)/form\.xls$",
            download_xlsform,
            name="download_xlsform"),
    re_path(r"^(?P<username>\w+)/forms/(?P<id_string>[^/]+)/form\.json",
            download_jsonform,
            name="download_jsonform"),
    re_path(r'^favicon\.ico',
            RedirectView.as_view(url='/static/images/favicon.ico')),
]
