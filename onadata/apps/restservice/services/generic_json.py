import json

import requests

from onadata.apps.restservice.RestServiceInterface import RestServiceInterface


class ServiceDefinition(RestServiceInterface):
    """
    @deprecated.
    Service returns True to make Celery task run successfully 
    """
    id = u'json'
    verbose_name = u'JSON POST'

    def send(self, url, data):
        return True

