import httplib2

from onadata.apps.restservice.RestServiceInterface import RestServiceInterface


class ServiceDefinition(RestServiceInterface):
    """
    @deprecated.
    Service returns True to make Celery task run successfully 
    """

    id = u'xml'
    verbose_name = u'XML POST'

    def send(self, url, data):
        return True

