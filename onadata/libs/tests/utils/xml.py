# coding: utf-8
from xml.dom import minidom

PYXFORM_CHANGED_STRINGS = [
    ' jr:preload="uid"',
    ''' calculate="concat('uuid:', uuid())"''',
    # ' xmlns:odk="http://www.opendatakit.org/xforms"',
    # '''<hint>GPS coordinates can only be collected when outside.</hint>''',
]


def pyxform_version_agnostic(xml):
    for str_ in PYXFORM_CHANGED_STRINGS:
        xml = xml.replace(str_, '')
    return xml


def is_equal_xml(source: str, target: str) -> bool:
    """
    Validates if `source` and `target` are identical whatever the order
    of node attributes

    See: https://stackoverflow.com/a/321941/1141214
    """

    def is_equal_element(a, b):
        if a.tagName != b.tagName:
            return False
        if sorted(a.attributes.items()) != sorted(b.attributes.items()):
            return False
        if len(a.childNodes) != len(b.childNodes):
            return False
        for ac, bc in zip(a.childNodes, b.childNodes):
            if ac.nodeType != bc.nodeType:
                return False
            if ac.nodeType == ac.TEXT_NODE and ac.data != bc.data:
                return False
            if (
                    ac.nodeType == ac.ELEMENT_NODE
                    and not is_equal_element(ac, bc)
            ):
                return False
        return True

    da, db = minidom.parseString(source), minidom.parseString(target)
    return is_equal_element(da.documentElement, db.documentElement)
