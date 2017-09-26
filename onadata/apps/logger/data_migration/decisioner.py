
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
        return {
            'new_fields': self.new_fields,
            'removed_fields': self.removed_fields,
            'modified_fields': self.modifications,
        }

    @staticmethod
    def reverse_changes(changes):
        return {
            'new_fields': changes.get('removed_fields', []),
            'removed_fields': changes.get('new_fields', []),
            'modified_fields': {
                v: k for k, v in changes.get('modified_fields', {}).items()
            }
        }

    def convert_changes_to_decisions(self, changes):
        new_fields_decisions = {
            self.DETERMINE_KEY + new_field: self.NEW_FIELD
            for new_field in changes.get('new_fields', [])
        }
        modified_fields = changes.get('modified_fields', {}).items()
        modified_fields_decisions = {
            self.DETERMINE_KEY + new_value: old_value
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
