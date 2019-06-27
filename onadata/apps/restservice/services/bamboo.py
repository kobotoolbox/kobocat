
from pybamboo.dataset import Dataset
from pybamboo.connection import Connection

from onadata.apps.restservice.RestServiceInterface import RestServiceInterface
from onadata.apps.logger.models import XForm
from onadata.libs.utils.bamboo import get_new_bamboo_dataset, get_bamboo_url


class ServiceDefinition(RestServiceInterface):
    """
    @deprecated.
    Service returns True to make Celery task run successfully 
    """

    id = u'bamboo'
    verbose_name = u'bamboo POST'

    def send(self, url, data):
        return True
