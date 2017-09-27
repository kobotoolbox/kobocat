from .migrate_data import DataMigrator, SurveyFieldsHandler
from .decisioner import MigrationDecisioner
from .compare_xml import XFormsComparator
from .backup_data import backup_xform


def migration_decisioner_factory(old_xform, new_xform, **request_data):
    xforms_comparator = XFormsComparator(old_xform.xml, new_xform.xml)
    migration_decisioner = MigrationDecisioner(xforms_comparator, **request_data)
    return migration_decisioner


def data_migrator_factory(old_xform, new_xform, backup_data=True, **request_data):
    migration_decisioner = migration_decisioner_factory(old_xform, new_xform,
                                                        **request_data)
    xform_backup = backup_xform(
        old_xform, new_xform.id, migration_decisioner.fields_changes,
    ) if backup_data else None

    fields_handler = SurveyFieldsHandler(migration_decisioner)
    data_migrator = DataMigrator(new_xform, fields_handler,
                                 backup_data, xform_backup)
    return data_migrator
