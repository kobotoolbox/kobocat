from django.conf.urls import patterns, include, url
from django.conf import settings
from django.views.generic import RedirectView

from onadata.apps.api.urls import router, router_with_patch_list
from onadata.apps.api.urls import XFormListApi
from onadata.apps.api.urls import XFormSubmissionApi
from onadata.apps.api.urls import BriefcaseApi

# Uncomment the next two lines to enable the admin:
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns(
    '',
    # change Language
    (r'^i18n/', include('django.conf.urls.i18n')),
    url('^api/v1/', include(router.urls)),
    url('^api/v1/', include(router_with_patch_list.urls)),
    url(r'^service_health/$',
        'onadata.apps.main.service_health.service_health'),
    url(r'^api-docs/', RedirectView.as_view(url='/api/v1/')),
    url(r'^api/', RedirectView.as_view(url='/api/v1/')),
    url(r'^api/v1', RedirectView.as_view(url='/api/v1/')),

    # django default stuff
    url(r'^accounts/', include('registration.auth_urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # oath2_provider
    url(r'^o/', include('oauth2_provider.urls', namespace='oauth2_provider')),

    # main website views
    url(r'^$', 'onadata.apps.main.views.home'),
    url(r'^forms/(?P<uuid>[^/]+)$', 'onadata.apps.main.views.show'),
    url(r'^login_redirect/$', 'onadata.apps.main.views.login_redirect'),
    # Bring back old url because it's still used by `kpi`
    # ToDo Remove when `kpi#gallery-2` is merged into master
    url(r"^attachment/$", 'onadata.apps.viewer.views.attachment_url'),
    url(r"^attachment/(?P<size>[^/]+)$",
        'onadata.apps.viewer.views.attachment_url'),
    url(r"^{}$".format(settings.MEDIA_URL.lstrip('/')), 'onadata.apps.viewer.views.attachment_url'),
    url(r"^{}(?P<size>[^/]+)$".format(settings.MEDIA_URL.lstrip('/')),
        'onadata.apps.viewer.views.attachment_url'),
    url(r'^jsi18n/$', 'django.views.i18n.javascript_catalog',
        {'packages': ('main', 'viewer',)}),
    url(r'^typeahead_usernames', 'onadata.apps.main.views.username_list',
        name='username_list'),
    url(r'^(?P<username>[^/]+)/$',
        'onadata.apps.main.views.profile', name='user_profile'),
    url(r'^(?P<username>[^/]+)/api-token$',
        'onadata.apps.main.views.api_token'),

    # form specific
    url(r'^(?P<username>[^/]+)/forms/(?P<id_string>[^/]+)$',
        'onadata.apps.main.views.show'),
    url(r'^(?P<username>[^/]+)/forms/(?P<id_string>[^/]+)/edit$',
        'onadata.apps.main.views.edit'),
    url(r'^(?P<username>[^/]+)/forms/(?P<id_string>[^/]+)/photos',
        'onadata.apps.main.views.form_photos'),
    url(r'^(?P<username>[^/]+)/forms/(?P<id_string>[^/]+)/formid-media/(?P<dat'
        'a_id>\d+)', 'onadata.apps.main.views.download_media_data'),
    url(r'^(?P<username>[^/]+)/forms/(?P<id_string>[^/]+)/form_settings$',
        'onadata.apps.main.views.show_form_settings', name='show_form_settings'),

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
        'onadata.apps.viewer.views.data_export', name='csv_export',
        kwargs={'export_type': 'csv'}),
    url(r"^(?P<username>\w+)/forms/(?P<id_string>[^/]+)/data\.xls",
        'onadata.apps.viewer.views.data_export', name='xls_export',
        kwargs={'export_type': 'xls'}),
    url(r"^(?P<username>\w+)/forms/(?P<id_string>[^/]+)/data\.kml$",
        'onadata.apps.viewer.views.kml_export'),
    url(r"^(?P<username>\w+)/exports/(?P<id_string>[^/]+)/(?P<export_type>\w+)"
        "/new$", 'onadata.apps.viewer.views.create_export'),
    url(r"^(?P<username>\w+)/exports/(?P<id_string>[^/]+)/(?P<export_type>\w+)"
        "/delete$", 'onadata.apps.viewer.views.delete_export'),
    url(r"^(?P<username>\w+)/exports/(?P<id_string>[^/]+)/(?P<export_type>\w+)"
        "/progress$", 'onadata.apps.viewer.views.export_progress'),
    url(r"^(?P<username>\w+)/exports/(?P<id_string>[^/]+)/(?P<export_type>\w+)"
        "/$", 'onadata.apps.viewer.views.export_list'),
    url(r"^(?P<username>\w+)/exports/(?P<id_string>[^/]+)/(?P<export_type>\w+)"
        "/(?P<filename>[^/]+)$",
        'onadata.apps.viewer.views.export_download'),
    url(r'^(?P<username>\w+)/exports/', include('onadata.apps.export.urls')),

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
        "/(?P<metadata>[\d+^/.]+)$",
        XFormListApi.as_view({'get': 'media'}), name='xform-media'),
    url(r"^(?P<username>\w+)/xformsMedia/(?P<pk>[\d+^/]+)"
        "/(?P<metadata>[\d+^/.]+)\.(?P<format>[a-z0-9]+)$",
        XFormListApi.as_view({'get': 'media'}), name='xform-media'),
    url(r"^xformsMedia/(?P<pk>[\d+^/]+)/(?P<metadata>[\d+^/.]+)$",
        XFormListApi.as_view({'get': 'media'}), name='xform-media'),
    url(r"^xformsMedia/(?P<pk>[\d+^/]+)/(?P<metadata>[\d+^/.]+)\."
        "(?P<format>[a-z0-9]+)$",
        XFormListApi.as_view({'get': 'media'}), name='xform-media'),
    url(r"^(?P<username>\w+)/submission$",
        XFormSubmissionApi.as_view({'post': 'create', 'head': 'create'}),
        name='submissions'),
    url(r"^(?P<username>\w+)/bulk-submission$",
        'onadata.apps.logger.views.bulksubmission'),
    url(r"^(?P<username>\w+)/bulk-submission-form$",
        'onadata.apps.logger.views.bulksubmission_form'),
    url(r"^(?P<username>\w+)/forms/(?P<pk>[\d+^/]+)/form\.xml$",
        XFormListApi.as_view({'get': 'retrieve'}),
        name="download_xform"),
    url(r"^(?P<username>\w+)/forms/(?P<id_string>[^/]+)/form\.xml$",
        'onadata.apps.logger.views.download_xform', name="download_xform"),
    url(r"^(?P<username>\w+)/forms/(?P<id_string>[^/]+)/form\.xls$",
        'onadata.apps.logger.views.download_xlsform',
        name="download_xlsform"),
    url(r"^(?P<username>\w+)/forms/(?P<id_string>[^/]+)/form\.json",
        'onadata.apps.logger.views.download_jsonform',
        name="download_jsonform"),

    url(r'^favicon\.ico',
        RedirectView.as_view(url='/static/images/favicon.ico')),

    # Statistics for superusers. The username is irrelevant, but leave it as
    # the first part of the path to avoid collisions
    url(r"^(?P<username>[^/]+)/superuser_stats/$",
        'onadata.apps.logger.views.superuser_stats'),
    url(r"^(?P<username>[^/]+)/superuser_stats/(?P<base_filename>[^/]+)$",
        'onadata.apps.logger.views.retrieve_superuser_stats'),

)

urlpatterns += patterns('django.contrib.staticfiles.views',
                        url(r'^static/(?P<path>.*)$', 'serve'))
