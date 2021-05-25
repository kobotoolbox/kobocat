# coding: utf-8

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
