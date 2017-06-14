'''
Django management command to populate `Instance` instances with hashes for use in duplicate
detection.

Relies solely on the `argparse` capabilities of `BaseCommand` for argument parsing and validation.


:Example:
    python manage.py populate_xml_hashes_for_instances --repopulate --usernames someuser anotheruser
    python manage.py populate_xml_hashes_for_instances --all
'''

from datetime import datetime

from django.core.management.base import BaseCommand

from ...models import Instance


class Command(BaseCommand):
    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument(
            '--all',
            action='store_true',
            help='Populate all `Instance` objects with hashes.',
        )
        group.add_argument(
            '--usernames',
            nargs='+',
            help='Space-delimited list of usernames whose `Instance` objects should be populated'
            ' with hashes.'
        )
        parser.add_argument(
            '--repopulate',
            action='store_true',
            help='''Don't skip over `Instance` objects that already have hashes.''',
        )

    def handle(self, *_, **options):
        # Copy arguments to be passed to `populate_xml_hashes_for_instances()`.
        populate_kwargs = {key: options[key] for key in ['usernames', 'repopulate']}

        # Populate the `Instance` hashes and track how long it took.
        start_time = datetime.now()
        instances_updated_total = Instance.populate_xml_hashes_for_instances(**populate_kwargs)
        execution_time = datetime.now() - start_time

        print('Populated {} `Instance` hashes in {}.'.format(instances_updated_total,
                                                             execution_time))
