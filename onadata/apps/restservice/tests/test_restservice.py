# coding: utf-8
from __future__ import unicode_literals, print_function, division, absolute_import

import os

from django.conf import settings

from onadata.apps.main.tests.test_base import TestBase
from onadata.apps.logger.models.xform import XForm
from onadata.apps.restservice.RestServiceInterface import RestServiceInterface
from onadata.apps.restservice.models import RestService


class RestServiceTest(TestBase):

    def setUp(self):
        super(RestServiceTest, self).setUp()
        xls_file_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'fixtures',
            'dhisform.xls'
        )
        self._publish_xls_file_and_set_xform(xls_file_path)

    def _create_rest_service(self):
        rs = RestService(
            service_url=settings.KPI_HOOK_ENDPOINT_PATTERN.format(
                asset_uid='aAAAAAAAAAAA'),
            xform=XForm.objects.all().reverse()[0],
            name='kpi_hook')
        rs.save()
        self.restservice = rs

    def test_create_rest_service(self):
        count = RestService.objects.all().count()
        self._create_rest_service()
        self.assertEquals(RestService.objects.all().count(), count + 1)

    def test_service_definition(self):
        self._create_rest_service()
        sv = self.restservice.get_service_definition()()
        self.assertEqual(isinstance(sv, RestServiceInterface), True)

