# coding: utf-8
from django.conf import settings
from django.contrib import admin
from django.contrib.staticfiles.views import serve
from django.urls import include, re_path
from django.views.generic import RedirectView
from django.views.i18n import JavaScriptCatalog

from onadata.apps.api.urls import BriefcaseApi
from onadata.apps.api.urls import XFormListApi
from onadata.apps.api.urls import XFormSubmissionApi
from onadata.apps.api.urls import router, router_with_patch_list
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

admin.autodiscover()

urlpatterns = [
    # re_path('') # Same as `re_path(r'^$', home)`?
    # change Language
    re_path(r'^i18n/', include('django.conf.urls.i18n')),
    re_path('^api/v1/', include(router.urls)),
    re_path('^api/v1/', include(router_with_patch_list.urls)),
    re_path(r'^service_health/$', service_health),
    re_path(r'^api-docs/', RedirectView.as_view(url='/api/v1/')),
    re_path(r'^api/', RedirectView.as_view(url='/api/v1/')),
    re_path(r'^api/v1', RedirectView.as_view(url='/api/v1/')),

    # django default stuff
    re_path(r'^accounts/', include('onadata.apps.main.registration_urls')),
    re_path(r'^admin/', admin.site.urls),
    re_path(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # oath2_provider
    re_path(r'^o/', include('oauth2_provider.urls', namespace='oauth2_provider')),

    # google urls
    re_path(r'^gauthtest/$', google_oauth2_request, name='google-auth'),
    re_path(r'^gwelcome/$', google_auth_return, name='google-auth-welcome'),

    # main website views
    re_path(r'^$', home),
    re_path(r'^tutorial/$', tutorial, name='tutorial'),
    re_path(r'^about-us/$', about_us, name='about-us'),
    re_path(r'^getting_started/$', getting_started,
            name='getting_started'),
    re_path(r'^faq/$', faq, name='faq'),
    re_path(r'^syntax/$', syntax, name='syntax'),
    re_path(r'^privacy/$', privacy, name='privacy'),
    re_path(r'^tos/$', tos, name='tos'),
    re_path(r'^resources/$', resources,
            name='resources'),
    re_path(r'^forms/$', form_gallery,
            name='forms_list'),
    re_path(r'^forms/(?P<uuid>[^/]+)$', show, name='show_form'),
    re_path(r'^people/$', members_list, name='members_list'),
    re_path(r'^xls2xform/$', xls2xform, name='xls2xform'),
    re_path(r'^support/$', support, name='support'),
    re_path(r'^login_redirect/$', login_redirect),
    # Bring back old url because it's still used by `kpi`
    # ToDo Remove when `kpi#gallery-2` is merged into master
    re_path(r"^attachment/$", attachment_url, name='attachment_url'),
    re_path(r"^attachment/(?P<size>[^/]+)$",
            attachment_url, name='attachment_url'),
    re_path(r"^{}$".format(settings.MEDIA_URL.lstrip('/')), attachment_url, name='attachment_url'),
    re_path(r"^{}(?P<size>[^/]+)$".format(settings.MEDIA_URL.lstrip('/')),
            attachment_url, name='attachment_url'),
    re_path(r'^jsi18n/$', JavaScriptCatalog.as_view(packages=['onadata.apps.main', 'onadata.apps.viewer']),
            name='javascript-catalog'),
    re_path(r'^typeahead_usernames', username_list,
            name='username_list'),
    re_path(r'^(?P<username>[^/]+)/$',
            profile, name='user_profile'),
    re_path(r'^(?P<username>[^/]+)/profile$',
            public_profile,
            name='public_profile'),
    re_path(r'^(?P<username>[^/]+)/settings',
            profile_settings, name='profile_settings'),
    re_path(r'^(?P<username>[^/]+)/cloneform$',
            clone_xlsform, name='clone_xlsform'),
    re_path(r'^(?P<username>[^/]+)/activity$',
            activity, name='activity'),
    re_path(r'^(?P<username>[^/]+)/activity/api$',
            activity_api, name='activity_api'),
    re_path(r'^activity/fields$', activity_fields, name='activity_fields'),
    re_path(r'^(?P<username>[^/]+)/api-token$',
            api_token, name='api_token'),

    # form specific
    re_path(r'^(?P<username>[^/]+)/forms/(?P<id_string>[^/]+)$',
            show, name='show_form'),
    re_path(r'^(?P<username>[^/]+)/forms/(?P<id_string>[^/]+)/qrcode$',
            qrcode, name='get_qrcode'),
    re_path(r'^(?P<username>[^/]+)/forms/(?P<id_string>[^/]+)/api$',
            api, name='mongo_view_api'),
    re_path(r'^(?P<username>[^/]+)/forms/(?P<id_string>[^/]+)/public_api$',
            public_api, name='public_api'),
    re_path(r'^(?P<username>[^/]+)/forms/(?P<id_string>[^/]+)/delete_data$',
            delete_data, name='delete_data'),
    re_path(r'^(?P<username>[^/]+)/forms/(?P<id_string>[^/]+)/edit$',
            edit, name='edit_form'),
    re_path(r'^(?P<username>[^/]+)/forms/(?P<id_string>[^/]+)/perms$',
            set_perm, name='set_perm'),
    re_path(r'^(?P<username>[^/]+)/forms/(?P<id_string>[^/]+)/photos',
            form_photos, name='form_photos'),
    re_path(r'^(?P<username>[^/]+)/forms/(?P<id_string>[^/]+)/doc/(?P<data_id>\d+)'
            '', download_metadata, name='download_metadata'),
    re_path(r'^(?P<username>[^/]+)/forms/(?P<id_string>[^/]+)/delete-doc/'
            r'(?P<data_id>\d+)', delete_metadata, name='delete_metadata'),
    re_path(r'^(?P<username>[^/]+)/forms/(?P<id_string>[^/]+)/formid-media/'
            r'(?P<data_id>\d+)', download_media_data, name='download_media_data'),
    re_path(r'^(?P<username>[^/]+)/forms/(?P<id_string>[^/]+)/update$',
            update_xform, name='update_xform'),
    re_path(r'^(?P<username>[^/]+)/forms/(?P<id_string>[^/]+)/preview$',
            enketo_preview, name='enketo_preview'),
    re_path(r'^(?P<username>[^/]+)/forms/(?P<id_string>[^/]+)/form_settings$',
            show_form_settings, name='show_form_settings'),

    # briefcase api urls
    re_path(r"^(?P<username>\w+)/view/submissionList$",
            BriefcaseApi.as_view({'get': 'list', 'head': 'list'}),
            name='view-submission-list'),
    re_path(r"^(?P<username>\w+)/view/downloadSubmission$",
            BriefcaseApi.as_view({'get': 'retrieve', 'head': 'retrieve'}),
            name='view-download-submission'),
    re_path(r"^(?P<username>\w+)/formUpload$",
            BriefcaseApi.as_view({'post': 'create', 'head': 'create'}),
            name='form-upload'),
    re_path(r"^(?P<username>\w+)/upload$",
            BriefcaseApi.as_view({'post': 'create', 'head': 'create'}),
            name='upload'),

    # exporting stuff
    re_path(r"^(?P<username>\w+)/forms/(?P<id_string>[^/]+)/data\.csv$",
            data_export, name='csv_export',
            kwargs={'export_type': 'csv'}),
    re_path(r"^(?P<username>\w+)/forms/(?P<id_string>[^/]+)/data\.xls",
            data_export, name='xls_export',
            kwargs={'export_type': 'xls'}),
    re_path(r"^(?P<username>\w+)/forms/(?P<id_string>[^/]+)/data\.csv.zip",
            data_export, name='csv_zip_export',
            kwargs={'export_type': 'csv_zip'}),
    re_path(r"^(?P<username>\w+)/forms/(?P<id_string>[^/]+)/data\.sav.zip",
            data_export, name='sav_zip_export',
            kwargs={'export_type': 'sav_zip'}),
    re_path(r"^(?P<username>\w+)/forms/(?P<id_string>[^/]+)/data\.kml$",
            kml_export, name='kml_export'),
    re_path(r"^(?P<username>\w+)/forms/(?P<id_string>[^/]+)/gdocs$",
            google_xls_export, name='google_xls_export'),
    re_path(r"^(?P<username>\w+)/forms/(?P<id_string>[^/]+)/map_embed",
            map_embed_view, name='map_embed_view'),
    re_path(r"^(?P<username>\w+)/forms/(?P<id_string>[^/]+)/map",
            map_view, name='map_view'),
    re_path(r"^(?P<username>\w+)/forms/(?P<id_string>[^/]+)/instance",
            instance, name='instance'),
    re_path(r"^(?P<username>\w+)/forms/(?P<id_string>[^/]+)/enter-data",
            enter_data, name='enter_data'),
    re_path(r"^(?P<username>\w+)/forms/(?P<id_string>[^/]+)/add-submission-with",
            add_submission_with,
            name='add_submission_with'),
    re_path(r"^(?P<username>\w+)/forms/(?P<id_string>[^/]+)/thank_you_submission",
            thank_you_submission,
            name='thank_you_submission'),
    re_path(r"^(?P<username>\w+)/forms/(?P<id_string>[^/]+)/edit-data/"
            r"(?P<data_id>\d+)$", edit_data, name='edit_data'),
    re_path(r"^(?P<username>\w+)/forms/(?P<id_string>[^/]+)/view-data",
            data_view, name='data_view'),
    re_path(r"^(?P<username>\w+)/exports/(?P<id_string>[^/]+)/(?P<export_type>\w+)"
            r"/new$", create_export, name='create_export'),
    re_path(r"^(?P<username>\w+)/exports/(?P<id_string>[^/]+)/(?P<export_type>\w+)"
            r"/delete$", delete_export, name='delete_export'),
    re_path(r"^(?P<username>\w+)/exports/(?P<id_string>[^/]+)/(?P<export_type>\w+)"
            r"/progress$", export_progress, name='export_progress'),
    re_path(r"^(?P<username>\w+)/exports/(?P<id_string>[^/]+)/(?P<export_type>\w+)"
            r"/$", export_list, name='export_list'),
    re_path(r"^(?P<username>\w+)/exports/(?P<id_string>[^/]+)/(?P<export_type>\w+)"
            r"/(?P<filename>[^/]+)$",
            export_download, name='export_download'),
    re_path(r'^(?P<username>\w+)/reports/', include('onadata.apps.survey_report.urls')),

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
    re_path(r"^(?P<username>\w+)/forms/(?P<pk>[\d+^/]+)/form\.xml$",
            XFormListApi.as_view({'get': 'retrieve'}),
            name="download_xform"),
    re_path(r"^(?P<username>\w+)/forms/(?P<id_string>[^/]+)/form\.xml$",
            download_xform, name="download_xform"),
    re_path(r"^(?P<username>\w+)/forms/(?P<id_string>[^/]+)/form\.xls$",
            download_xlsform,
            name="download_xlsform"),
    re_path(r"^(?P<username>\w+)/forms/(?P<id_string>[^/]+)/form\.json",
            download_jsonform,
            name="download_jsonform"),
    re_path(r"^(?P<username>\w+)/delete/(?P<id_string>[^/]+)/$",
            delete_xform, name='delete_xform'),
    re_path(r"^(?P<username>\w+)/(?P<id_string>[^/]+)/toggle_downloadable/$",
            toggle_downloadable, name='toggle_downloadble'),

    # SMS support
    re_path(r'^(?P<username>[^/]+)/forms/(?P<id_string>[^/]+)/sms_submission/'
            r'(?P<service>[a-z]+)/?$',
            import_submission_for_form,
            name='sms_submission_form_api'),
    re_path(r'^(?P<username>[^/]+)/forms/(?P<id_string>[^/]+)/sms_submission$',
            view_import_submission_for_form,
            name='sms_submission_form'),
    re_path(r"^(?P<username>[^/]+)/sms_submission/(?P<service>[a-z]+)/?$",
            import_submission,
            name='sms_submission_api'),
    re_path(r'^(?P<username>[^/]+)/forms/(?P<id_string>[^/]+)/'
            r'sms_multiple_submissions$',
            import_multiple_submissions_for_form,
            name='sms_submissions_form'),
    re_path(r"^(?P<username>[^/]+)/sms_multiple_submissions$",
            import_multiple_submissions,
            name='sms_submissions'),
    re_path(r"^(?P<username>[^/]+)/sms_submission$",
            view_import_submission,
            name='sms_submission'),

    # static media
    # Media are now served by NginX.
    # re_path(r'^media/(?P<path>.*)$', 'django.views.static.serve',
    #    {'document_root': settings.MEDIA_ROOT}),
    re_path(r'^static/(?P<path>.*)$', serve),

    re_path(r'^favicon\.ico',
            RedirectView.as_view(url='/static/images/favicon.ico')),

    # Statistics for superusers. The username is irrelevant, but leave it as
    # the first part of the path to avoid collisions
    re_path(r"^(?P<username>[^/]+)/superuser_stats/$",
            superuser_stats),
    re_path(r"^(?P<username>[^/]+)/superuser_stats/(?P<base_filename>[^/]+)$",
            retrieve_superuser_stats),
]
