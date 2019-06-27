import httplib2
import requests

from onadata.apps.restservice.RestServiceInterface import RestServiceInterface


class ServiceDefinition(RestServiceInterface):
    """
    @deprecated.
    Service returns True to make Celery task run successfully 
    """

    id = u'f2dhis2'
    verbose_name = u'Formhub to DHIS2'

    def send(self, url, data):
        return True

    def send_ziggy(self, url, ziggy_instance, uuid):
        return True
