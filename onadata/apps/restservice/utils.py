import logging
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from onadata.apps.restservice import SERVICE_CHOICES
from onadata.apps.restservice.models import RestService

valid_service_names = (x[0] for x in SERVICE_CHOICES)

def call_service(parsed_instance):
    # lookup service
    instance = parsed_instance.instance

    # check for a forced service
    if settings.FORCE_REST_SERVICE_NAME:
        if not settings.FORCE_REST_SERVICE_URL:
            raise ImproperlyConfigured(
                'You must specify FORCE_REST_SERVICE_URL when setting '
                'FORCE_REST_SERVICE_NAME'
            )
        if settings.FORCE_REST_SERVICE_NAME not in valid_service_names:
            raise ImproperlyConfigured(
                'FORCE_REST_SERVICE_NAME specifies a service not listed in '
                'onadata.apps.restservice.SERVICE_CHOICES'
            )
        RestService.objects.get_or_create(
            xform=instance.xform,
            name=settings.FORCE_REST_SERVICE_NAME,
            service_url=settings.FORCE_REST_SERVICE_URL
        )

    services = RestService.objects.filter(xform=instance.xform)
    # call service send with url and data parameters
    for sv in services:
        # TODO: Queue service
        try:
            service = sv.get_service_definition()()
            service.send(sv.service_url, parsed_instance)
        except:
            if settings.FAILED_REST_SERVICE_BLOCKS_SUBMISSION:
                raise
            else:
                # TODO: Handle gracefully | requeue/resend
                pass


def call_ziggy_services(ziggy_instance, uuid):
    # we can only handle f2dhis2 services at this time
    services = RestService.objects.filter(xform=ziggy_instance.xform,
                                          name='f2dhis2')
    services_called = 0
    for sv in services:
        # TODO: Queue service
        try:
            service = sv.get_service_definition()()
            response = service.send_ziggy(sv.service_url, ziggy_instance, uuid)
        except:
            # TODO: Handle gracefully | requeue/resend
            pass
        else:
            if response is not None and response.status_code == 200:
                services_called += 1
    return services_called
