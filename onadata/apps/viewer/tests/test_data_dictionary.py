import os
import json

from django.test import TestCase
from django.contrib.auth.models import User
from onadata.apps.logger.models.xform import title_pattern

from onadata.libs.utils.viewer_tools import django_file
from onadata.apps.viewer.models import DataDictionary


class TestDataDictionary(TestCase):
    def test_set_title_in_xml(self):
        this_directory = os.path.dirname(__file__)
        fixture = os.path.join(this_directory, 'fixtures', 'test_data_types',
                               'test_data_types.xls')

        data_dictionary = DataDictionary.objects.create(
            xml="""
            <h:html>
                <instance>
                    <a3Yb9EqQKDYPLf8RgymtXp id="a3Yb9EqQKDYPLf8RgymtXp"
                                            version="vQDVGC3CQDtHXtGWizAncT">
                    </a3Yb9EqQKDYPLf8RgymtXp>
                </instance>

                <h:head> <h:title>Old title</h:title> <instance> </h:head>
                <h:body> <input> <label>Name</label> </input> </h:body>
            </h:html>
            """,
            user=User.objects.create_user(username='user', password='passwd123'),
            xls=django_file(fixture, 'file', 'text/xml')
        )
        data_dictionary.json = json.dumps({
                'name': 'Name',
                'title': 'Desired title',
                'type': 'Type'
            })
        data_dictionary._set_title_in_xml()
        data_dictionary_title = title_pattern.findall(data_dictionary.xml)[0]
        self.assertEqual(data_dictionary_title, 'Desired title')
