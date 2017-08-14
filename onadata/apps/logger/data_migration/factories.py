from .migrate_data import DataMigrator, SurveyFieldsHandler
from .decisioner import MigrationDecisioner
from .compare_xml import XFormsComparator


def migration_decisioner_factory(old_xform, new_xform, **request_data):
    xforms_comparator = XFormsComparator(old_xform.xml, new_xform.xml)
    migration_decisioner = MigrationDecisioner(xforms_comparator, **request_data)
    return migration_decisioner


def data_migrator_factory(old_xform, new_xform, **request_data):
    migration_decisioner = migration_decisioner_factory(old_xform, new_xform,
                                                        **request_data)
    fields_handler = SurveyFieldsHandler(migration_decisioner)
    data_migrator = DataMigrator(new_xform, fields_handler)
    return data_migrator
