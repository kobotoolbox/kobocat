# coding: utf-8
from __future__ import unicode_literals, print_function, division, absolute_import
import os

from django.test import TestCase
from django.utils.encoding import smart_text

from onadata.apps.main.google_doc import GoogleDoc


class TestGoogleDoc(TestCase):

    def test_view(self):
        doc = GoogleDoc()
        folder = os.path.join(
            os.path.dirname(__file__), "fixtures", "google_doc"
            )
        input_path = os.path.join(folder, "input.html")
        with open(input_path) as f:
            input_html = smart_text(f.read())
        doc.set_html(input_html)
        self.assertEqual(doc._html, input_html)
        self.assertEqual(len(doc._sections), 14)
        output_path = os.path.join(folder, "navigation.html")
        with open(output_path) as f:
            self.assertEquals(doc._navigation_html(), f.read())
