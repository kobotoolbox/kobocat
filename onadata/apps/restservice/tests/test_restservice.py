import os
import time

from django.core.urlresolvers import reverse
from nose import SkipTest
from pybamboo.connection import Connection
from pybamboo.dataset import Dataset

from onadata.apps.main.views import show, link_to_bamboo
from onadata.apps.main.tests.test_base import TestBase
from onadata.apps.logger.models.xform import XForm
from onadata.apps.restservice.RestServiceInterface import RestServiceInterface
from onadata.apps.restservice.models import RestService


class RestServiceTest(TestBase):

    def setUp(self):
        self.service_url = u'http://0.0.0.0:8001/%(id_string)s/post/%(uuid)s'
        self.service_name = u'f2dhis2'
        self._create_user_and_login()
        filename = u'dhisform.xls'
        self.this_directory = os.path.dirname(__file__)
        path = os.path.join(self.this_directory, u'fixtures', filename)
        self._publish_xls_file(path)
        self.xform = XForm.objects.all().reverse()[0]

    def wait(self, t=1):
        time.sleep(t)

    def _create_rest_service(self):
        rs = RestService(service_url=self.service_url,
                         xform=self.xform, name=self.service_name)
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

