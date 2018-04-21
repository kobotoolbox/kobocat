from onadata.apps.logger.models.instance import save_survey

from .surveytree import SurveyTree, MissingFieldException
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

    @staticmethod
    def set_proper_root_node(xform, survey_tree):
        new_root_id = xform.id_string
        survey_tree.change_field_tag(survey_tree.root, new_root_id)
        survey_tree.set_field_attrib(survey_tree.root, attrib='id',
                                     new_value=new_root_id)

    def migrate_survey(self, survey):
        survey_tree = SurveyTree(survey)
        self.set_proper_root_node(self.xform, survey_tree)
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

    def add_fields(self, survey_tree, new_fields_tags):
        for field_to_add_tag in new_fields_tags:
            text = self.decisioner.get_prepopulate_text(field_to_add_tag)
            groups = self.decisioner.fields_groups_new().get(field_to_add_tag, [])
            try:
                survey_tree.get_field(field_to_add_tag)
            except MissingFieldException:
                field = survey_tree.create_element(field_to_add_tag, text)
                survey_tree.insert_field_into_group_chain(field, groups)

    def modify_fields(self, survey_tree, modifications):
        for prev_tag, new_tag in modifications.iteritems():
            groups = self.decisioner.fields_groups_new().get(prev_tag, [])
            field = survey_tree.get_or_create_field(prev_tag, groups=groups)
            survey_tree.change_field_tag(field, new_tag)

    def migrate_groups(self, survey_tree):
        changed_fields_groups = self.decisioner.changed_fields_groups()
        for field_tag, groups in changed_fields_groups.iteritems():
            self._migrate_field_groups(survey_tree, field_tag, groups)

    def _migrate_field_groups(self, survey_tree, field_tag, groups):
        try:
            field = survey_tree.get_field(field_tag)
            survey_tree.permanently_remove_field(field)
        except MissingFieldException:
            field = survey_tree.create_element(field_tag)
        survey_tree.insert_field_into_group_chain(field, groups)
