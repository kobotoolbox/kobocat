# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from onadata.apps.main.tests.test_base import TestBase
from onadata.apps.logger.models.xform import XForm
from onadata.apps.restservice.RestServiceInterface import RestServiceInterface
from onadata.apps.restservice.models import RestService


class RestServiceTest(TestBase):

    def _create_rest_service(self):
        rs = RestService(service_url='/api/v2/assets/aAAAAAAAAAAA/hook-signal/',
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

