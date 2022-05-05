from xml.etree.ElementTree import fromstring, tostring, SubElement

from onadata.libs.utils import common_tags

def inject_veritree_app_version_into_xml(xml, app_version):
    if not app_version:
        return xml
    root = fromstring(xml)
    if root:
        # Its safer to only care about veritree_app_versions in the meta
        # tag that is a direct child of root
        metaTag = root.find('meta')
        if metaTag:
            existing_veritree_app_version = metaTag.find(common_tags.VERITREE_APP_VERSION)
            if not existing_veritree_app_version:
                app_version_element = SubElement(metaTag, common_tags.VERITREE_APP_VERSION)
                app_version_element.text = app_version
                return tostring(root)
    return xml
