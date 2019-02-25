# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from onadata.apps.restservice.models import RestService
from onadata.apps.restservice.tasks import service_definition_task


def call_service(parsed_instance):
    # lookup service
    instance = parsed_instance.instance
    rest_services = RestService.objects.filter(xform=instance.xform)
    # call service send with url and data parameters
    for rest_service in rest_services:
        # Celery can't pickle ParsedInstance object,
        # let's use build a serializable object instead
        # We don't really need `xform_id`, `xform_id_string`, `instance_uuid`
        # We use them only for retro compatibility with all services (even if they are deprecated)
        data = {
            "xform_id": instance.xform.id,
            "xform_id_string": instance.xform.id_string,
            "instance_uuid": instance.uuid,
            "instance_id": instance.id,
            "xml": parsed_instance.instance.xml,
            "json": parsed_instance.to_dict_for_mongo()
        }
        service_definition_task.delay(rest_service.pk, data)


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
