import json

import requests

from onadata.apps.restservice.RestServiceInterface import RestServiceInterface


class ServiceDefinition(RestServiceInterface):
    """
        @deprecated.
        This service should not be used anymore.
    """
    id = u'json'
    verbose_name = u'JSON POST'

    def send(self, url, data):
        post_data = json.dumps(data.get("json"))
        headers = {"Content-Type": "application/json"}
        requests.post(url, headers=headers, data=post_data)
