
NEW_FIELDS_KEY = 'new_fields'
RM_FIELDS_KEY = 'removed_fields'
MOD_FIELDS_KEY = 'modified_fields'


class MigrationDecisioner(object):
    """
    This class provides an neat encapsulation of user decisions format.
    Migration decisions format specification:

    1) determine_<new_field_name>: <field_name>
      Each tag of given <field_name> will be updated with new,
      modified value. Data remains unchanged.
      Use case: user fix typo in field name

    2) determine_<field_name>: __new_field__

    3) prepopulate_<field_name>: <value>
      For each previous record (survey answer), fill new field (<field_name>)
      with given value.

    Example:
    decisions = {
        'determine_gender': 'geender',
        'determine_age': '__new_field__',
        'prepopulate_name': 'Martin',
        'prepopulate_last_name': 'Fowler',
    }
    """
    NEW_FIELD = '__new_field__'
    DETERMINE_KEY = 'determine_'
    PREPOPULATE_KEY = 'prepopulate_'

    def __init__(self, xforms_comparator, **data):
        self._decisions = self._extract_migration_decisions(**data)
        self.xforms_comparator = xforms_comparator

        added, potentiall_removed = self.xforms_comparator.fields_diff()
        self.removed_fields = self.get_removed_fields(potentiall_removed)
        self.new_fields = self.get_new_fields(added)
        self.modifications = self.get_fields_modifications(potentiall_removed)

    @property
    def fields_changes(self):
        """Return migration changes. Spec:

        :list new_fields: new fields in migration
        :list removed_fields: removed fields in migration
        :dict modifications: describes variable renaming decisions. Format:
            {<prev_name>: <new_name>}
        """
        return {
            NEW_FIELDS_KEY: self.new_fields,
            RM_FIELDS_KEY: self.removed_fields,
            MOD_FIELDS_KEY: self.modifications,
        }

    @staticmethod
    def construct_changes(new=None, removed=None, modified=None):
        """Invoke function withot parameters to get empty changes template"""
        return {
            NEW_FIELDS_KEY: new or [],
            RM_FIELDS_KEY: removed or [],
            MOD_FIELDS_KEY: modified or {},
        }

    @classmethod
    def reverse_changes(cls, changes):
        return cls.construct_changes(**{
            'new': changes.get(RM_FIELDS_KEY),
            'removed': changes.get(NEW_FIELDS_KEY),
            'modified': {
                v: k for k, v in changes.get(MOD_FIELDS_KEY, {}).items()
            }
        })

    @classmethod
    def convert_changes_to_decisions(cls, changes):
        new_fields_decisions = {
            cls.DETERMINE_KEY + new_field: cls.NEW_FIELD
            for new_field in changes.get(NEW_FIELDS_KEY, [])
        }
        modified_fields = changes.get(MOD_FIELDS_KEY, {}).items()
        modified_fields_decisions = {
            cls.DETERMINE_KEY + new_value: old_value
            for old_value, new_value in modified_fields
        }
        new_fields_decisions.update(modified_fields_decisions)
        return new_fields_decisions

    def _extract_migration_decisions(self, **data):
        def get_value(value):
            return value[0] if isinstance(value, list) else value
        return {
            key: get_value(value) for key, value in data.iteritems()
            if self.PREPOPULATE_KEY in key or self.DETERMINE_KEY in key
        }

    def _get_determined_field(self, field_name):
        return self._decisions.get(self.DETERMINE_KEY + field_name)

    def _get_decision_key_by_value(self, field_name):
        for key, value in self._decisions.iteritems():
            if value == field_name:
                return key.replace(self.DETERMINE_KEY, '')
        return ''

    def get_prepopulate_text(self, field_name):
        return self._decisions.get(self.PREPOPULATE_KEY + field_name) or ''

    def get_removed_fields(self, potentially_removed):
        return [
            removed_field for removed_field in potentially_removed
            if not self._get_decision_key_by_value(removed_field)
        ]

    def get_new_fields(self, added):
        return [
            added_field for added_field in added
            if self._get_determined_field(added_field) == self.NEW_FIELD
        ]

    def get_fields_modifications(self, potentially_removed):
        decision_values = map(self._get_decision_key_by_value,
                              potentially_removed)
        return {
            p_removed_field: decision_val
            for p_removed_field, decision_val in zip(potentially_removed,
                                                     decision_values)
            if decision_val and decision_val != self.NEW_FIELD
        }
