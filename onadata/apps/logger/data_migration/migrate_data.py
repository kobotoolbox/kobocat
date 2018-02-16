from onadata.apps.logger.models.instance import save_survey
from .surveytree import SurveyTree
from . import backup_data


class DataMigrator(object):
    """
    Adjust survey answers in database to new schema defined by updated xform.
    Create backup of each previous survey answer.

    Database can be adjusted up to user decisions. User can tell:
    - Which new fields should be *prepopulated* with any constant value.
      All the previous records will share common value.
    - Can *determine* which fields are modified, and which are the new ones
    """
    def __init__(self, xform, fields_handler,
                 backup_data=True, xform_backup=None):
        self.xform = xform
        self.fields_handler = fields_handler
        self.backup_data = backup_data
        self.xform_backup = xform_backup

    @property
    def decisioner(self):
        return self.fields_handler.decisioner

    def __call__(self):
        self.migrate()

    def count_surveys(self, xform):
        return xform.instances.all().count()

    def get_surveys_iter(self, xform):
        return xform.instances.iterator()

    def migrate_survey(self, survey):
        survey_tree = SurveyTree(survey)
        self.fields_handler.alter_fields(survey_tree)
        survey.xml = survey_tree.to_string()
        save_survey(survey)

    def migrate(self):
        for survey in self.get_surveys_iter(self.xform):
            if self.backup_data:
                backup_data.backup_survey(survey, self.xform_backup)
            self.migrate_survey(survey)


class SurveyFieldsHandler(object):
    """Handle fields operations."""
    def __init__(self, migration_decisioner):
        self.decisioner = migration_decisioner

    def alter_fields(self, survey_tree):
        self.add_fields(survey_tree, self.decisioner.new_fields)
        self.modify_fields(survey_tree, self.decisioner.modifications)
        self.migrate_groups(survey_tree)

    def add_fields(self, survey_tree, new_fields):
        for field_to_add in new_fields:
            text = self.decisioner.get_prepopulate_text(field_to_add)
            survey_tree.add_field(field_to_add, text)

    def modify_fields(self, survey_tree, modifications):
        for prev_field, new_field in modifications.iteritems():
            survey_tree.modify_field(prev_field, new_field)

    def migrate_groups(self, survey_tree):
        changed_fields_groups = self.decisioner.changed_fields_groups()
        for field_name, groups in changed_fields_groups.iteritems():
            self._migrate_field_groups(survey_tree, field_name, groups)

    def _migrate_field_groups(self, survey_tree, field_name, groups):
        field = survey_tree.permanently_remove_field(field_name)
        survey_tree.insert_field_into_group_chain(field, groups)

