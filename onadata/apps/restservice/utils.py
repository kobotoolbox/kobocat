# coding: utf-8
from onadata.apps.restservice.models import RestService
from onadata.apps.restservice.tasks import service_definition_task
from onadata.libs.utils.common_tags import HOOK_EVENT


def call_service(parsed_instance, event=HOOK_EVENT['ON_SUBMIT']):
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
            "json": parsed_instance.to_dict_for_mongo(),
            "event": event
        }
        service_definition_task.delay(rest_service.pk, data)
