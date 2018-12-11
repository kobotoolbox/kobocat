import httplib2

from onadata.apps.restservice.RestServiceInterface import RestServiceInterface


class ServiceDefinition(RestServiceInterface):
    """
        @deprecated.
        This service should not be used anymore.
    """

    id = u'xml'
    verbose_name = u'XML POST'

    def send(self, url, data):
        headers = {"Content-Type": "application/xml"}
        http = httplib2.Http()
        resp, content = http.request(
            url, method="POST", body=data.get("xml"), headers=headers)
