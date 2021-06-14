# coding: utf-8
from __future__ import unicode_literals, print_function, division, absolute_import
import os
import reversion
import unittest

from onadata.apps.main.tests.test_base import TestBase
from onadata.apps.logger.models import XForm, Instance


class TestXForm(TestBase):
    def test_set_title_in_xml_unicode_error(self):
        xls_file_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "../..",  "fixtures", "tutorial", "tutorial_arabic_labels.xls"
        )
        self._publish_xls_file_and_set_xform(xls_file_path)

        self.assertTrue(isinstance(self.xform.xml, unicode))

        # change title
        self.xform.title = 'Random Title'

        self.assertNotIn(self.xform.title, self.xform.xml)

        # convert xml to str
        self.xform.xml = self.xform.xml.encode('utf-8')
        self.assertTrue(isinstance(self.xform.xml, str))

        # set title in xform xml
        self.xform._set_title()
        self.assertIn(self.xform.title, self.xform.xml)

    @unittest.skip('Fails under Django 1.6')
    def test_reversion(self):
        self.assertTrue(reversion.is_registered(XForm))
