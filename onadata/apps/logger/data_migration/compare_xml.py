from .xformtree import XFormTree


class XFormsComparator(object):
    """
    Compare XML of two xforms.

    This parser looks for differences between added / removed / modified:
    - title
    - fields
    - fields types
    - field obligations
    - selects values

    Output human readable results afterwards

    Example XML files are available in
    `onadata.apps.logger.tests.data_migration.fixtures`
    """
    def __init__(self, prev_xml, new_xml):
        self.prev_tree = XFormTree(prev_xml)
        self.new_tree = XFormTree(new_xml)

    def __str__(self):
        return self.comparison_results()

    def clean_tag(self, tag):
        return self.prev_tree.clean_tag(tag)

    def fields_diff(self):
        """
        Difference between fields. Returns tuple of two lists where
        first one contains added and second one contains
        removed fields in new xml form file.
        """
        added = self.new_tree.added_fields(self.prev_tree)
        removed = self.prev_tree.added_fields(self.new_tree)
        return added, removed

    def fields_type_diff(self):
        """
        Differences between fields types.
        Returns dictionary with changed types
        Output: {'field_name': 'changed_type'}
        """
        prev_types = self.prev_tree.get_fields_types()
        new_types = self.new_tree.get_fields_types()
        return {
            key: new_types[key]
            for key, val in prev_types.items()
            if key in new_types and val != new_types[key]
        }

    def titles_diff(self):
        if self.prev_tree.get_title() != self.new_tree.get_title():
            return self.new_tree.get_title()
        return ''

    def selects_diff(self):
        """
        Checks whether select have any new or removed options.
        Returns tuple of two dictionaries with added and removed values
        Example: {'gender': ['unknown']}
        """
        added = self.new_tree.added_select_options(self.prev_tree)
        removed = self.prev_tree.added_select_options(self.new_tree)
        return added, removed

    def input_obligation_diff(self):
        """Difference if inputs became (un)required."""
        prev_oblig = self.prev_tree.get_fields_obligation()
        new_oblig = self.new_tree.get_fields_obligation()
        return {
            key: new_oblig[key]
            for key, val in prev_oblig.items()
            if key in new_oblig and val != new_oblig[key]
        }

    def pprint_dict(self, **data):
        result = ''
        for key, val in data.items():
            result += "Name: {}, new value: {}\n".format(key, val)
        return result or ''

    def comparison_results(self):
        return {
            'new_title': (self.titles_diff() or ''),
            'fields_added': self.fields_diff()[0],
            'fields_removed': self.fields_diff()[1],
            'fields_type_diff': self.pprint_dict(**self.fields_type_diff()),
            'input_obligation_diff': (
                self.pprint_dict(**self.input_obligation_diff()))
        }
