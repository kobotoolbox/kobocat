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
        """Get field in tree by name."""
        matching_elems = self._get_matching_elems(lambda f: f.tag == name)
        return self._get_first_element(name)(matching_elems)

    @classmethod
    def get_child_field(cls, element, name):
        """Get child of element by name"""
        return compose(
            cls._get_first_element(name),
            partial(ifilter, lambda f: f.tag == name),
        )(element)

    def permanently_remove_field(self, field):
        """WARNING: It is not possible to revert this operation"""
        field.getparent().remove(field)

    def change_field_tag(self, field, new_tag):
        field.tag = new_tag

    def set_field_attrib(self, field, attrib, new_value):
        field.attrib[attrib] = new_value

    def get_or_create_field(self, field_tag, text='', groups=None):
        groups = groups if groups is not None else []
        try:
            field = self.get_field(field_tag)
        except MissingFieldException:
            field = self.create_element(field_tag, text)
            self.insert_field_into_group_chain(field, groups)
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

        for group_tag in group_chain:
            try:
                group_field = self.get_child_field(parent, group_tag)
            except MissingFieldException:
                group_field = self.create_element(group_tag)
                parent.append(group_field)
            parent = group_field

        parent.append(field)
