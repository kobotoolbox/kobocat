### ISSUE 242 TEMPORARY FIX ###
# See https://github.com/kobotoolbox/kobocat/issues/242

from celery import shared_task
from django.core.management import call_command

@shared_task(soft_time_limit=600, time_limit=900)
def fix_root_node_names(minimum_instance_id):
    call_command(
        'fix_root_node_names',
        minimum_instance_id=minimum_instance_id,
    )

###### END ISSUE 242 FIX ######
