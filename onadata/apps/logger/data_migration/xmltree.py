from lxml import etree

from .common import concat_map


def encode_xml_to_ascii(xml):
    # Without proper encoding, lxml throws ValueError for Unicode string.
    return xml.decode('utf-8').encode('ascii')


class XMLTree(object):
    """
    Common class for handling XML trees
    """
    # XML elements that should not be considered as fields
    NOT_RELEVANT = ['formhub', 'meta', 'imei', '__version__']

    def __init__(self, xml):
        self.root = etree.XML(encode_xml_to_ascii(xml))

    def __repr__(self):
        return self.to_string()

    def to_string(self, pretty=True):
        return etree.tostring(self.root, pretty_print=pretty)

    def to_xml(self, pretty=True):
        return etree.tostring(self.root, pretty_print=pretty,
                              xml_declaration=True, encoding='utf-8')

    @classmethod
    def retrieve_leaf_elems(cls, element):
        if not cls.is_relevant(element.tag):
            return []
        if element.getchildren():
            return concat_map(cls.retrieve_leaf_elems, element)
        return [element]

    @classmethod
    def retrieve_leaf_elems_tags(cls, element):
        return map(cls.field_tag, cls.retrieve_leaf_elems(element))

    @classmethod
    def retrieve_groups(cls, element):
        if not cls.is_relevant(element.tag) or not element.getchildren():
            return []
        return [element] + concat_map(cls.retrieve_groups, element)

    @classmethod
    def retrieve_all_elems(cls, element):
        if not cls.is_relevant(element.tag):
            return []
        return [element] + concat_map(cls.retrieve_all_elems, element)

    @classmethod
    def is_relevant(cls, tag):
        return cls.clean_tag(tag) not in cls.NOT_RELEVANT

    @classmethod
    def is_group(cls, element):
        return element.getchildren() and cls.is_relevant(element.tag)

    @staticmethod
    def create_element(field_name, text=''):
        return etree.XML('<{name}>{text}</{name}>'.format(name=field_name,
                                                          text=text))

    @staticmethod
    def clean_tag(tag):
        """
        Remove w3 header that tag may contain.
        Example: '{http://www.w3.org/1999/xhtml}head'
        """
        header_end = tag.find('}')
        return tag[header_end+1:] if header_end != -1 else tag

    @classmethod
    def field_tag(cls, field):
        return cls.clean_tag(field.tag)
