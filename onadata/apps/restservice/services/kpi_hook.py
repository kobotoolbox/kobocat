# -*- coding: utf-8 -*-
import json
import requests

from django.conf import settings
from onadata.apps.restservice.RestServiceInterface import RestServiceInterface


class ServiceDefinition(RestServiceInterface):
    id = u"kpi_hook"
    verbose_name = u"KPI Hook POST"

    def send(self, endpoint, parsed_instance):
        post_data = json.dumps(parsed_instance.to_dict_for_mongo())
        headers = {"Content-Type": "application/json"}
        # Build the url in the service to avoid saving hardcoded domain name in the DB
        url = "{}{}".format(
            settings.KPI_INTERNAL_URL,
            endpoint
        )
        try:
            response = requests.post(url, headers=headers, data=post_data)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            # TODO Save failure in ParseInstance or Instance for later retries
            pass