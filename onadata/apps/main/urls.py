# coding: utf-8
from django.conf.urls import include, url
from django.conf import settings
from django.contrib import admin
from django.contrib.staticfiles.views import serve
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
    tutorial,
    about_us,
    getting_started,
    faq,
    syntax,
    privacy,
    tos,
    resources,
    form_gallery,
    members_list,
    xls2xform,
    support,
    login_redirect,
    username_list,
    profile,
    public_profile,
    profile_settings,
    clone_xlsform,
    activity,
    activity_api,
    activity_fields,
    api_token,

    # form specific
    show,
    qrcode,
    api,
    public_api,
    delete_data,
    edit,
    set_perm,
    form_photos,
    download_metadata,
    delete_metadata,
    download_media_data,
    update_xform,
    enketo_preview,
    show_form_settings
)

# exporting stuff
from onadata.apps.viewer.views import (
    attachment_url,
    data_export,
    google_xls_export,
    map_embed_view,
    map_view,
    instance,
    add_submission_with,
    thank_you_submission,
    data_view,
    create_export,
    delete_export,
    export_progress,
    export_list,
    export_download,
    kml_export
)
from onadata.apps.logger.views import (
    enter_data,
    edit_data,
    bulksubmission,
    bulksubmission_form,
    download_xform,
    download_xlsform,
    download_jsonform,
    delete_xform,
    toggle_downloadable
)

# SMS support
from onadata.apps.sms_support.providers import (
    import_submission_for_form,
    import_submission
)
from onadata.apps.sms_support.views import (
    import_submission_for_form as view_import_submission_for_form,
    import_multiple_submissions_for_form,
    import_multiple_submissions,
    import_submission as view_import_submission
)
# Statistics for superusers. The username is irrelevant, but leave it as
# the first part of the path to avoid collisions
from onadata.apps.logger.views import (
    superuser_stats,
    retrieve_superuser_stats
)

from onadata.apps.main.google_export import (
    google_auth_return,
    google_oauth2_request
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
    url(r'^accounts/', include('onadata.apps.main.registration_urls')),
    url(r'^admin/', admin.site.urls),
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # oath2_provider
    url(r'^o/', include('oauth2_provider.urls', namespace='oauth2_provider')),

    # google urls
    url(r'^gauthtest/$', google_oauth2_request, name='google-auth'),
    url(r'^gwelcome/$', google_auth_return, name='google-auth-welcome'),

    # main website views
    url(r'^$', home),
    url(r'^tutorial/$', tutorial, name='tutorial'),
    url(r'^about-us/$', about_us, name='about-us'),
    url(r'^getting_started/$', getting_started,
        name='getting_started'),
    url(r'^faq/$', faq, name='faq'),
    url(r'^syntax/$', syntax, name='syntax'),
    url(r'^privacy/$', privacy, name='privacy'),
    url(r'^tos/$', tos, name='tos'),
    url(r'^resources/$', resources,
        name='resources'),
    url(r'^forms/$', form_gallery,
        name='forms_list'),
    url(r'^forms/(?P<uuid>[^/]+)$', show, name='show_form'),
    url(r'^people/$', members_list, name='members_list'),
    url(r'^xls2xform/$', xls2xform, name='xls2xform'),
    url(r'^support/$', support, name='support'),
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
    url(r'^typeahead_usernames', username_list,
        name='username_list'),
    url(r'^(?P<username>[^/]+)/$',
        profile, name='user_profile'),
    url(r'^(?P<username>[^/]+)/profile$',
        public_profile,
        name='public_profile'),
    url(r'^(?P<username>[^/]+)/settings',
        profile_settings, name='profile_settings'),
    url(r'^(?P<username>[^/]+)/cloneform$',
        clone_xlsform, name='clone_xlsform'),
    url(r'^(?P<username>[^/]+)/activity$',
        activity, name='activity'),
    url(r'^(?P<username>[^/]+)/activity/api$',
        activity_api, name='activity_api'),
    url(r'^activity/fields$', activity_fields, name='activity_fields'),
    url(r'^(?P<username>[^/]+)/api-token$',
        api_token, name='api_token'),

    # form specific
    url(r'^(?P<username>[^/]+)/forms/(?P<id_string>[^/]+)$',
        show, name='show_form'),
    url(r'^(?P<username>[^/]+)/forms/(?P<id_string>[^/]+)/qrcode$',
        qrcode, name='get_qrcode'),
    url(r'^(?P<username>[^/]+)/forms/(?P<id_string>[^/]+)/api$',
        api, name='mongo_view_api'),
    url(r'^(?P<username>[^/]+)/forms/(?P<id_string>[^/]+)/public_api$',
        public_api, name='public_api'),
    url(r'^(?P<username>[^/]+)/forms/(?P<id_string>[^/]+)/delete_data$',
        delete_data, name='delete_data'),
    url(r'^(?P<username>[^/]+)/forms/(?P<id_string>[^/]+)/edit$',
        edit, name='edit_form'),
    url(r'^(?P<username>[^/]+)/forms/(?P<id_string>[^/]+)/perms$',
        set_perm, name='set_perm'),
    url(r'^(?P<username>[^/]+)/forms/(?P<id_string>[^/]+)/photos',
        form_photos, name='form_photos'),
    url(r'^(?P<username>[^/]+)/forms/(?P<id_string>[^/]+)/doc/(?P<data_id>\d+)'
        '', download_metadata, name='download_metadata'),
    url(r'^(?P<username>[^/]+)/forms/(?P<id_string>[^/]+)/delete-doc/'
        r'(?P<data_id>\d+)', delete_metadata, name='delete_metadata'),
    url(r'^(?P<username>[^/]+)/forms/(?P<id_string>[^/]+)/formid-media/'
        r'(?P<data_id>\d+)', download_media_data, name='download_media_data'),
    url(r'^(?P<username>[^/]+)/forms/(?P<id_string>[^/]+)/update$',
        update_xform, name='update_xform'),
    url(r'^(?P<username>[^/]+)/forms/(?P<id_string>[^/]+)/preview$',
        enketo_preview, name='enketo_preview'),
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
    url(r"^(?P<username>\w+)/forms/(?P<id_string>[^/]+)/data\.csv.zip",
        data_export, name='csv_zip_export',
        kwargs={'export_type': 'csv_zip'}),
    url(r"^(?P<username>\w+)/forms/(?P<id_string>[^/]+)/data\.sav.zip",
        data_export, name='sav_zip_export',
        kwargs={'export_type': 'sav_zip'}),
    url(r"^(?P<username>\w+)/forms/(?P<id_string>[^/]+)/data\.kml$",
        kml_export, name='kml_export'),
    url(r"^(?P<username>\w+)/forms/(?P<id_string>[^/]+)/gdocs$",
        google_xls_export, name='google_xls_export'),
    url(r"^(?P<username>\w+)/forms/(?P<id_string>[^/]+)/map_embed",
        map_embed_view, name='map_embed_view'),
    url(r"^(?P<username>\w+)/forms/(?P<id_string>[^/]+)/map",
        map_view, name='map_view'),
    url(r"^(?P<username>\w+)/forms/(?P<id_string>[^/]+)/instance",
        instance, name='instance'),
    url(r"^(?P<username>\w+)/forms/(?P<id_string>[^/]+)/enter-data",
        enter_data, name='enter_data'),
    url(r"^(?P<username>\w+)/forms/(?P<id_string>[^/]+)/add-submission-with",
        add_submission_with,
        name='add_submission_with'),
    url(r"^(?P<username>\w+)/forms/(?P<id_string>[^/]+)/thank_you_submission",
        thank_you_submission,
        name='thank_you_submission'),
    url(r"^(?P<username>\w+)/forms/(?P<id_string>[^/]+)/edit-data/"
        r"(?P<data_id>\d+)$", edit_data, name='edit_data'),
    url(r"^(?P<username>\w+)/forms/(?P<id_string>[^/]+)/view-data",
        data_view, name='data_view'),
    url(r"^(?P<username>\w+)/exports/(?P<id_string>[^/]+)/(?P<export_type>\w+)"
        r"/new$", create_export, name='create_export'),
    url(r"^(?P<username>\w+)/exports/(?P<id_string>[^/]+)/(?P<export_type>\w+)"
        r"/delete$", delete_export, name='delete_export'),
    url(r"^(?P<username>\w+)/exports/(?P<id_string>[^/]+)/(?P<export_type>\w+)"
        r"/progress$", export_progress, name='export_progress'),
    url(r"^(?P<username>\w+)/exports/(?P<id_string>[^/]+)/(?P<export_type>\w+)"
        r"/$", export_list, name='export_list'),
    url(r"^(?P<username>\w+)/exports/(?P<id_string>[^/]+)/(?P<export_type>\w+)"
        r"/(?P<filename>[^/]+)$",
        export_download, name='export_download'),
    url(r'^(?P<username>\w+)/reports/', include('onadata.apps.survey_report.urls')),

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
    url(r"^(?P<username>\w+)/delete/(?P<id_string>[^/]+)/$",
        delete_xform, name='delete_xform'),
    url(r"^(?P<username>\w+)/(?P<id_string>[^/]+)/toggle_downloadable/$",
        toggle_downloadable, name='toggle_downloadble'),

    # SMS support
    url(r'^(?P<username>[^/]+)/forms/(?P<id_string>[^/]+)/sms_submission/'
        r'(?P<service>[a-z]+)/?$',
        import_submission_for_form,
        name='sms_submission_form_api'),
    url(r'^(?P<username>[^/]+)/forms/(?P<id_string>[^/]+)/sms_submission$',
        view_import_submission_for_form,
        name='sms_submission_form'),
    url(r"^(?P<username>[^/]+)/sms_submission/(?P<service>[a-z]+)/?$",
        import_submission,
        name='sms_submission_api'),
    url(r'^(?P<username>[^/]+)/forms/(?P<id_string>[^/]+)/'
        r'sms_multiple_submissions$',
        import_multiple_submissions_for_form,
        name='sms_submissions_form'),
    url(r"^(?P<username>[^/]+)/sms_multiple_submissions$",
        import_multiple_submissions,
        name='sms_submissions'),
    url(r"^(?P<username>[^/]+)/sms_submission$",
        view_import_submission,
        name='sms_submission'),

    # static media
    # Media are now served by NginX.
    # url(r'^media/(?P<path>.*)$', 'django.views.static.serve',
    #    {'document_root': settings.MEDIA_ROOT}),
    url(r'^static/(?P<path>.*)$', serve),

    url(r'^favicon\.ico',
        RedirectView.as_view(url='/static/images/favicon.ico')),

    # Statistics for superusers. The username is irrelevant, but leave it as
    # the first part of the path to avoid collisions
    url(r"^(?P<username>[^/]+)/superuser_stats/$",
        superuser_stats),
    url(r"^(?P<username>[^/]+)/superuser_stats/(?P<base_filename>[^/]+)$",
        retrieve_superuser_stats),
]
