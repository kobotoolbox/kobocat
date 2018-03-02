from functools import partial
from itertools import ifilter
from lxml import etree

from .xmltree import XMLTree
from .common import compose, concat_map


class MissingFieldException(Exception):
    pass


class SurveyTree(XMLTree):
    """
    Parse XForm Instance from xml string into tree.
    """
    def __init__(self, survey):
        # Handle both cases when instance or string is passed.
        try:
            self.root = etree.XML(survey.xml)
        except AttributeError:
            self.root = etree.XML(survey)

    def get_fields(self):
        """Parse and return list of all fields in form."""
        return self.retrieve_leaf_elems(self.root)

    def get_groups(self):
        return concat_map(self.retrieve_groups, self.root.getchildren())

    def get_all_elems(self):
        """Return a list of both groups and fields"""
        return concat_map(self.retrieve_all_elems, self.root.getchildren())

    def get_fields_names(self):
        """Return fields as list of string with field names."""
        return map(lambda f: f.tag, self.get_fields())

    def get_groups_names(self):
        """Return fields as list of string with field names."""
        return map(lambda g: g.tag, self.get_groups())

    def _get_matching_elems(self, condition_func):
        """Return elems that match condition"""
        return ifilter(condition_func, self.get_all_elems())

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
        matching_elems = self._get_matching_elems(lambda f: f.tag == name)
        return self._get_first_element(name)(matching_elems)

    def permanently_remove_field(self, field_name):
        """WARNING: It is not possible to revert this operation"""
        field = self.get_field(field_name)
        field.getparent().remove(field)
        return field

    def modify_field(self, field_name, new_tag):
        field = self.get_field(field_name)
        field.tag = new_tag

    def add_field(self, field_name, text='', parent=None):
        parent = parent if parent is not None else self.root
        try:
            field = self.get_field(field_name)
        except MissingFieldException:
            field = self.create_element(field_name)
            field.text = text
            parent.append(field)
        return field

    def find_group(self, name):
        """Find group named :group_name: or throw exception"""
        return compose(
            self._get_first_element(name),
            partial(ifilter, lambda e: e.tag == name),
        )(self.get_groups())

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
