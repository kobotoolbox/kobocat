### ISSUE 242 TEMPORARY FIX ###
# See https://github.com/kobotoolbox/kobocat/issues/242

from celery import shared_task
from django.core.management import call_command

@shared_task(soft_time_limit=600, time_limit=900)
def fix_root_node_names(**kwargs):
    call_command(
        'fix_root_node_names',
        **kwargs
    )

###### END ISSUE 242 FIX ######

import csv
import datetime
import pytz
import zipfile
from io import BytesIO
from collections import defaultdict
from django.contrib.auth.models import User
from django.core.files.storage import get_storage_class
from .models import Instance, XForm

@shared_task
def generate_stats_zip(output_filename):
    REPORTS = {
        'instances.csv': {
            'model': Instance,
            'date_field': 'date_created'
        },
        'xforms.csv': {
            'model': XForm,
            'date_field': 'date_created'
        },
        'users.csv': {
            'model': User,
            'date_field': 'date_joined'
        }
    }

    def list_created_by_month(model, date_field):
        # Make a single, huge query to the database
        data_dump = list(model.objects.values_list('pk', date_field))
        # Sort by date
        data_dump = sorted(data_dump, key=lambda x: x[1])

        year_month_counts = defaultdict(lambda: defaultdict(lambda: 0))
        last_pks = defaultdict(lambda: defaultdict(lambda: 0))
        for pk, date in data_dump:
            year_month_counts[date.year][date.month] += 1
            last_pks[date.year][date.month] = pk

        results = []
        cumulative = 0
        for year in sorted(year_month_counts.keys()):
            for month in sorted(year_month_counts[year].keys()):
                cumulative += year_month_counts[year][month]
                results.append((
                    year, month, year_month_counts[year][month],
                    cumulative, last_pks[year][month]
                ))

        return results

    default_storage = get_storage_class()()
    with default_storage.open(output_filename, 'wb') as output_file:
        zip_file = zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED)
        for filename, report_settings in REPORTS.iteritems():
            model_name_plural = report_settings[
                'model']._meta.verbose_name_plural
            fieldnames = [
                'Year',
                'Month',
                'New {}'.format(model_name_plural.capitalize()),
                'Cumulative {}'.format(model_name_plural.capitalize()),
                'Last Primary Key (possible clue about deleted objects)',
            ]
            data = list_created_by_month(
                report_settings['model'], report_settings['date_field'])
            csv_io = BytesIO()
            writer = csv.DictWriter(csv_io, fieldnames=fieldnames)
            writer.writeheader()
            for row in data:
                writer.writerow(dict(zip(fieldnames, row)))
            zip_file.writestr(filename, csv_io.getvalue())
            csv_io.close()

        zip_file.close()
