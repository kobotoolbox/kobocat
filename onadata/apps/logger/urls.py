from django.conf.urls import patterns, url


urlpatterns = patterns(
    '',
    url(r'(?P<old_id_string>[^/]+)/(?P<new_id_string>[^/]+)/update-and-migrate$',
        'onadata.apps.logger.data_migration.views.xform_migration_gui',
        name='xform-migration-gui'),

    url(r'(?P<id_string>[^/]+)/api-data-migration$',
        'onadata.apps.logger.data_migration.views.api_data_migration',
        name='api-migration-endpoint'),
    url(r'(?P<id_string>[^/]+)/migrate-view$',
        'onadata.apps.logger.data_migration.views.pre_migration_view',
        name='pre-migration-view'),
    url(r'(?P<id_string>[^/]+)/update-and-migrate$',
        'onadata.apps.logger.data_migration.views.update_xform_and_prepare_migration',
        name='update-xform-and-prepare-migration'),

    url(r'(?P<old_id_string>[^/]+)/(?P<new_id_string>[^/]+)/migrate-data$',
        'onadata.apps.logger.data_migration.views.migrate_xform_data',
        name='migrate-xform-data'),
    url(r'(?P<old_id_string>[^/]+)/(?P<new_id_string>[^/]+)/abandon-migration$',
        'onadata.apps.logger.data_migration.views.abandon_xform_data_migration',
        name='abandon-xform-data-migration'),
)
