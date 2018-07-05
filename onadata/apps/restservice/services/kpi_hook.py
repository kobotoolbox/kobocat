# -*- coding: utf-8 -*-
import logging
import json
import requests

from django.conf import settings
from onadata.apps.restservice.RestServiceInterface import RestServiceInterface


class ServiceDefinition(RestServiceInterface):
    id = u"kpi_hook"
    verbose_name = u"KPI Hook POST"

    def send(self, endpoint, parsed_instance):

        post_data = {
            "xml": parsed_instance.instance.xml,
            "json": parsed_instance.to_dict(),
            "uid": parsed_instance.instance.uuid,  # Will be used to expose data in API
            "id": parsed_instance.instance.id  # Will be used internally by KPI to retry in case of failure
        }
        headers = {"Content-Type": "application/json"}
        # Build the url in the service to avoid saving hardcoded domain name in the DB
        url = "{}{}".format(
            settings.KPI_INTERNAL_URL,
            endpoint
        )
        try:
            response = requests.post(url, headers=headers, json=post_data)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger = logging.getLogger("console_logger")
            logger.error("KPI Hook - ServiceDefinition.send - {}".format(str(e)))
            # TODO Save failure in ParseInstance or Instance for later retries
            pass