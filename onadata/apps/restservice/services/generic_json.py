import json

import requests

from onadata.apps.restservice.RestServiceInterface import RestServiceInterface


class ServiceDefinition(RestServiceInterface):
    id = u'json'
    verbose_name = u'JSON POST'

    def send(self, url, parsed_instance):
        post_data = json.dumps(parsed_instance.to_dict_for_mongo())
        headers = {"Content-Type": "application/json"}
        requests.post(url, headers=headers, data=post_data)
