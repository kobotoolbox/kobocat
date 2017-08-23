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
    def __init__(self, xform, fields_handler):
        self.xform = xform
        self.fields_handler = fields_handler

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
        survey.save()
        survey.parsed_instance.save(async=True)

    def migrate(self):
        backup_xform = backup_data.backup_xform(self.xform)
        for survey in self.get_surveys_iter(self.xform):
            backup_data.backup_survey(survey, backup_xform)
            self.migrate_survey(survey)


class SurveyFieldsHandler(object):
    """Handle fields operations."""
    def __init__(self, migration_decisioner):
        self.decisioner = migration_decisioner

    def alter_fields(self, survey_tree):
        self.add_fields(survey_tree, self.decisioner.new_fields)
        self.remove_fields(survey_tree, self.decisioner.removed_fields)
        self.modify_fields(survey_tree, self.decisioner.modifications)

    def add_fields(self, survey_tree, new_fields):
        for field_to_add in new_fields:
            text = self.decisioner.get_prepopulate_text(field_to_add)
            survey_tree.add_field(field_to_add, text)

    def remove_fields(self, survey_tree, removed):
        for field_to_remove in removed:
            survey_tree.remove_field(field_to_remove)

    def modify_fields(self, survey_tree, modifications):
        for prev_field, new_field in modifications.iteritems():
            survey_tree.modify_field(prev_field, new_field)
