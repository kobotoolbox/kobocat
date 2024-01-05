# coding: utf-8
from django.test import TestCase
from onadata.apps.main.context_processors import site_name


class CustomContextProcessorsTest(TestCase):
    def test_site_name(self):
        context = site_name(None)
        self.assertEqual(context, {'SITE_NAME': 'kc.kobotoolbox.org'})
