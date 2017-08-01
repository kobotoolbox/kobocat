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

    def first_day_of_next_month(any_date):
        return datetime.date(
            year=any_date.year if any_date.month < 12 else any_date.year + 1,
            month=any_date.month + 1 if any_date.month < 12 else 1,
            day=1
        )

    def first_day_of_previous_month(any_date):
        return datetime.date(
            year=any_date.year if any_date.month > 1 else any_date.year - 1,
            month=any_date.month - 1 if any_date.month > 1 else 12,
            day=1
        )

    def utc_midnight(any_date):
        return datetime.datetime(
            year=any_date.year,
            month=any_date.month,
            day=any_date.day,
            tzinfo=pytz.UTC
        )

    def list_created_by_month(model, date_field):
        today = datetime.date.today()
        # Just start at January 1 of the previous year. Going back to the
        # oldest object would be great, but it's too slow right now. Django
        # 1.10 will provide a more efficient way:
        # https://docs.djangoproject.com/en/1.10/ref/models/database-functions/#trunc
        first_date = datetime.date(
            year=today.year - 1,
            month=1,
            day=1
        )
        # We *ASSUME* that primary keys increase cronologically!
        last_object = model.objects.order_by('pk').last()
        last_date = first_day_of_next_month(getattr(last_object, date_field))
        year_month_count = []
        while last_date > first_date:
            this_start_date = first_day_of_previous_month(last_date)
            this_end_date = last_date
            criteria = {
                '{}__gte'.format(date_field): utc_midnight(this_start_date),
                '{}__lt'.format(date_field): utc_midnight(this_end_date)
            }
            objects_this_month = model.objects.filter(**criteria).count()
            year_month_count.append((
                this_start_date.year,
                this_start_date.month,
                objects_this_month
            ))
            last_date = this_start_date
        return year_month_count

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
                'NOTE: Records created prior to January 1 of last '
                'year are NOT included in this report!'
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
