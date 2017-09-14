

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

    def __init__(self, xforms_comparator, **data):
        self._decisions = self._extract_migration_decisions(**data)
        self.xforms_comparator = xforms_comparator

        added, potentiall_removed = self.xforms_comparator.fields_diff()
        self.removed_fields = self.get_removed_fields(potentiall_removed)
        self.new_fields = self.get_new_fields(added)
        self.modifications = self.get_fields_modifications(potentiall_removed)

    def _extract_migration_decisions(self, **data):
        def get_value(value):
            return value[0] if isinstance(value, list) else value
        return {
            key: get_value(value) for key, value in data.iteritems()
            if 'prepopulate_' in key or 'determine_' in key
        }

    def _get_determined_field(self, field_name):
        return self._decisions.get('determine_' + field_name)

    def _get_decision_key_by_value(self, field_name):
        for key, value in self._decisions.iteritems():
            if value == field_name:
                return key.replace('determine_', '')
        return ''

    def get_prepopulate_text(self, field_name):
        return self._decisions.get('prepopulate_' + field_name) or ''

    def get_removed_fields(self, potentiall_removed):
        return [
            removed_field for removed_field in potentiall_removed
            if not self._get_decision_key_by_value(removed_field)
        ]

    def get_new_fields(self, added):
        return [
            added_field for added_field in added
            if self._get_determined_field(added_field) == self.NEW_FIELD
        ]

    def get_fields_modifications(self, potentiall_removed):
        result = {}
        for removed_field in potentiall_removed:
            decision_val = self._get_decision_key_by_value(removed_field)
            if decision_val and decision_val != self.NEW_FIELD:
                result.update({removed_field: decision_val})
        return result
