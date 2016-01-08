import os
import json
import csv

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from optparse import make_option
from onadata.apps.logger.models import Instance
from onadata.apps.logger.models import XForm

INSTANCE_REPORT_FILE = '/tmp/instances.csv'
XFORM_REPORT_FILE = '/tmp/xforms.csv'
USER_REPORT_FILE = '/tmp/users.csv'

def _date(dd):
    return dd.strftime('%D-%T')

def sanitize(ii):
    ii['date_created'] = _date(ii['date_created'])
    return ii

def write_csv(filename, fieldnames, data):
    with open(filename, 'w') as out_file:
        writer = csv.DictWriter(out_file, fieldnames=fieldnames)
        writer.writeheader()
        for d in data:
            writer.writerow(d)

def _print_instances():
    fields = ('status', 'date_created', 'pk', 'user_id', 'xform_id')
    instances = Instance.objects.all().values(*fields)
    data = [sanitize(ii) for ii in instances]
    write_csv(INSTANCE_REPORT_FILE, fields, data)

def _print_xforms():
    fields = ('date_created', 'num_of_submissions', 'pk', 'user_id')
    xforms = XForm.objects.all().values(*fields)
    data = [sanitize(ii) for ii in xforms]
    write_csv(XFORM_REPORT_FILE, fields, data)

def _print_users():
    fields = ('date_joined', 'last_login', 'pk')
    users = User.objects.all().values(*fields)
    write_csv(USER_REPORT_FILE, fields, users)

class Command(BaseCommand):
    def handle(self, *args, **options):
        print 'Writing xforms report to "{}"...'.format(XFORM_REPORT_FILE)
        _print_xforms()
        print 'Writing instancess report to "{}"...'.format(INSTANCE_REPORT_FILE)
        _print_instances()
        print 'Writing users report to "{}"...'.format(USER_REPORT_FILE)
        _print_users()

