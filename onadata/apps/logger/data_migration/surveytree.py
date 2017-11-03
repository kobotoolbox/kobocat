from lxml import etree


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

    def get_field(self, name):
        """Get field Element by name."""
        fields = self.get_fields()
        for field in fields:
            if field.tag == name:
                return field
        raise MissingFieldException("Field name '{}' does not exist in survey tree".format(name))

    def create_element(self, field_name):
        return etree.XML('<{name}></{name}>'.format(name=field_name))

    def permanently_remove_field(self, field_name):
        """WARNING: It is not possible to revert this operation"""
        field = self.get_field(field_name)
        field.getparent().remove(field)

    def modify_field(self, field_name, new_tag):
        field = self.get_field(field_name)
        field.tag = new_tag

    def add_field(self, field_name, text=''):
        try:
            self.get_field(field_name)
        except MissingFieldException:
            field = self.create_element(field_name)
            field.text = text
            self.root.append(field)
