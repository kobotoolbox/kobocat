import hashlib
import json
import requests
from lxml import etree
from StringIO import StringIO

from django.conf import settings
from reversion.models import Version

from onadata.apps.restservice.RestServiceInterface import RestServiceInterface


class ServiceDefinition(RestServiceInterface):
    ''' This service ERASES all submission data in Postgres and Mongo except
    whatever is contained within the XML elements specified in
    `XML_CHILDREN_OF_ROOT_TO_KEEP`. The SHA256 of the submission's original
    JSON is also saved. That original JSON is then POSTed to the specified URL.
    Use with extreme caution! '''

    XML_CHILDREN_OF_ROOT_TO_KEEP = ('formhub', 'meta')
    id = u'destructive_json'
    verbose_name = u'DESTRUCTIVE JSON POST'

    def redact_submission(self, parsed_instance, append_elements=[]):
        instance = parsed_instance.instance
        xml_parser = etree.parse(StringIO(instance.xml))
        xml_root = xml_parser.getroot()
        # remove all user-generated data!
        for child in xml_root.getchildren():
            if child.tag not in self.XML_CHILDREN_OF_ROOT_TO_KEEP:
                xml_root.remove(child)

        # append any specified new elements before saving
        for el_to_append in append_elements:
            xml_root.append(el_to_append)

        instance.xml = etree.tounicode(xml_root)
        del instance._parser # has cached copy of xml
        del parsed_instance._dict_cache # cached copy of json
        instance.save()

        # delete revisions!
        Version.objects.get_for_object(instance).delete()

    def send(self, url, parsed_instance):
        post_data = json.dumps(parsed_instance.to_dict_for_mongo())
        hasher = hashlib.sha256()
        hasher.update(post_data)
        post_data_hash = hasher.hexdigest()
        hash_element = etree.Element('sha256')
        hash_element.text = post_data_hash

        self.redact_submission(parsed_instance, [hash_element])

        headers = {"Content-Type": "application/json"}
        response = requests.post(
            url, headers=headers, data=post_data, timeout=60)
        response.raise_for_status()
