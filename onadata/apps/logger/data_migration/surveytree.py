from functools import partial
from lxml import etree

from .common import compose


class MissingFieldException(Exception):
    pass


class SurveyTree(object):
    """
    Parse XForm Instance from xml string into tree.
    """
    # XML elements that should not be considered as fields
    NOT_RELEVANT = ['formhub', 'meta', 'imei']

    def __init__(self, survey):
        # Handle both cases when instance or string is passed.
        try:
            self.root = etree.XML(survey.xml)
        except AttributeError:
            self.root = etree.XML(survey)

    def __repr__(self):
        return self.to_string()

    def to_string(self, pretty=True):
        return etree.tostring(self.root, pretty_print=pretty)

    def get_fields(self):
        """Return fields as list with tree Elements."""
        return [
            field for field in self.root.getchildren()
            if field.tag not in self.NOT_RELEVANT
        ]

    def get_fields_names(self):
        """Return fields as list of string with field names."""
        return [
            field.tag for field in self.root.getchildren()
            if field.tag not in self.NOT_RELEVANT
        ]

    def _get_matching_fields(self, condition_func):
        """Return fields that match condition"""
        return iter(filter(condition_func, self.get_fields()))

    @staticmethod
    def _get_first_element(name):
        def get_next_from_iterator(iterator):
            try:
                return next(iterator)
            except StopIteration:
                raise MissingFieldException("Element '{}' does not exist in "
                                            "survey tree".format(name))
        return get_next_from_iterator

    def get_field(self, name):
        """Get field Element by name."""
        matching_fields = self._get_matching_fields(lambda f: f.tag == name)
        return self._get_first_element(name)(matching_fields)

    def create_element(self, field_name):
        return etree.XML('<{name}></{name}>'.format(name=field_name))

    def permanently_remove_field(self, field_name):
        """WARNING: It is not possible to revert this operation"""
        field = self.get_field(field_name)
        field.getparent().remove(field)
        return field

    def modify_field(self, field_name, new_tag):
        field = self.get_field(field_name)
        field.tag = new_tag

    def add_field(self, field_name, text='', parent=None):
        parent = parent or self.root
        try:
            field = self.get_field(field_name)
        except MissingFieldException:
            field = self.create_element(field_name)
            field.text = text
            parent.append(field)
        return field

    def find_group(self, name):
        """Find group named :group_name: or throw exception"""
        matching_fields = self._get_matching_fields(lambda f: f.tag == name)
        return compose(
            self._get_first_element(name),
            iter,
            partial(filter, lambda e: e.getchildren != []),
        )(matching_fields)

    def insert_field_into_group_chain(self, field, group_chain):
        """Insert field into a chain of groups. Function handles group field
        creation if one does not exist
        """
        assert etree.iselement(field)
        parent = self.root

        for group in group_chain:
            group_field = self.add_field(group, parent=parent)
            parent = group_field

        parent.append(field)

