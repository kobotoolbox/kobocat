from django.conf.urls import patterns, url

from onadata.apps.logger.data_migration import views


urlpatterns = patterns(
    '',
    url(r'(?P<old_id_string>[^/]+)/(?P<new_id_string>[^/]+)/update-and-migrate$',
        views.xform_migration_gui,
        name='xform-migration-gui'),

    url(r'(?P<id_string>[^/]+)/api-data-migration$',
        views.DataMigrationEndpoint.as_view(),
        name='api-migration-endpoint'),
    url(r'(?P<id_string>[^/]+)/migrate-view$',
        views.pre_migration_view,
        name='pre-migration-view'),
    url(r'(?P<id_string>[^/]+)/update-and-migrate$',
        views.update_xform_and_prepare_migration,
        name='update-xform-and-prepare-migration'),

    url(r'(?P<old_id_string>[^/]+)/(?P<new_id_string>[^/]+)/migrate-data$',
        views.migrate_xform_data,
        name='migrate-xform-data'),
    url(r'(?P<old_id_string>[^/]+)/(?P<new_id_string>[^/]+)/abandon-migration$',
        views.abandon_xform_data_migration,
        name='abandon-xform-data-migration'),
)
