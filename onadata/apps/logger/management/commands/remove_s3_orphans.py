#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import codecs
import re
import sys
import time

from django.core.management.base import BaseCommand, CommandError
from django.core.files.storage import get_storage_class
from django.db import connection
from django.db.models import Value as V
from django.db.models.functions import Concat
from django.utils.translation import ugettext as _, ugettext_lazy

from onadata.apps.logger.models import Attachment
from onadata.apps.viewer.models import Export

# S3 Monkey Patch
import boto
from boto import handler
from boto.resultset import ResultSet
from boto.s3.bucket import Bucket
import xml.sax
import xml.sax.saxutils


def _get_all(self, element_map, initial_query_string='',
             headers=None, **params):
    query_args = self._get_all_query_args(
        params,
        initial_query_string=initial_query_string
    )
    response = self.connection.make_request('GET', self.name,
                                            headers=headers,
                                            query_args=query_args)
    body = response.read()

    if response.status == 200:
        rs = ResultSet(element_map)
        h = handler.XmlHandler(rs, self)
        try:
            xml.sax.parseString(fix_bad_characters(body), h)
        except Exception as e:
            print("XML Parsing Error - {}".format(str(e)))
            error_filename = "/srv/logs/s3_body_error-{}.xml".format(str(int(time.time())))
            with open(error_filename, "w") as xmlfile_error:
                xmlfile_error.write("{}\n".format(str(e)))
                xmlfile_error.write(body)
            raise Exception(str(e))
        return rs
    else:
        raise self.connection.provider.storage_response_error(
            response.status, response.reason, body)


def fix_bad_characters(str_):

    try:
        str_ = re.sub(r"&(?!(quot|apos|lt|gt|amp);)", "&amp;", str_)
    except Exception as e:
        # Try to force unicode
        str_ = re.sub(r"&(?!(quot|apos|lt|gt|amp);)", "&amp;", unicode(str_, "utf-8"))
        str_ = str_.encode("utf-8")
    return str_


class Command(BaseCommand):
    help = ugettext_lazy("Removes attachments orphans from S3")

    def handle(self, *args, **kwargs):

        Bucket._get_all = _get_all

        s3 = get_storage_class('storages.backends.s3boto.S3BotoStorage')()
        all_files = s3.bucket.list()
        size_to_reclaim = 0
        orphans = 0

        now = time.time()
        csv_filepath = "/srv/logs/ocha_s3_orphans.csv"

        with open(csv_filepath, "w") as csv:
            csv.write("type,filename,filesize\n")

        for f in all_files:
            try:
                filename = f.name
                if filename[-1] != "/":
                    if re.match(r"[^\/]*\/attachments\/[^\/]*\/[^\/]*\/.+", filename):
                        clean_filename = filename
                        for auto_suffix in ["-large", "-medium", "-small"]:
                            if filename[-(len(auto_suffix) + 4):-4] == auto_suffix:
                                clean_filename = filename[:-(len(auto_suffix) + 4)] + filename[-4:]
                                break

                        if not Attachment.objects.filter(media_file=clean_filename).exists():
                            filesize = f.size
                            orphans += 1
                            size_to_reclaim += filesize
                            csv = codecs.open(csv_filepath, "a", "utf-8")
                            csv.write("{},{},{}\n".format("attachment", filename, filesize))
                            csv.close()
                            print("File {} does not exist".format(filename))

                    elif re.match(r"[^\/]*\/exports\/[^\/]*\/[^\/]*\/.+", filename):
                        #KC Export
                        if not Export.objects.annotate(fullpath=Concat("filedir",
                                                                       V("/"), "filename"))\
                                .filter(fullpath=filename).exists():
                            filesize = f.size
                            orphans += 1
                            size_to_reclaim += filesize
                            csv = codecs.open(csv_filepath, "a", "utf-8")
                            csv.write("{},{},{}\n".format("attachment", filename, filesize))
                            csv.close()
                            print("File {} does not exist".format(filename))

                    elif re.match(r"[^\/]*\/exports\/.+", filename):
                        #KPI Export
                        does_exist = False
                        with connection.cursor() as cursor:
                            cursor.execute("SELECT EXISTS(SELECT id FROM kpi_exporttask WHERE result = %s)", [filename])
                            try:
                                row = cursor.fetchone()
                                does_exist = row[0]
                            except:
                                pass

                        if not does_exist:
                            filesize = f.size
                            orphans += 1
                            size_to_reclaim += filesize
                            csv = codecs.open(csv_filepath, "a", "utf-8")
                            csv.write("{},{},{}\n".format("attachment", filename, filesize))
                            csv.close()
                            print("File {} does not exist".format(filename))

                if time.time() - now >= 5 * 60:
                    print("[{}] Still alive...".format(str(int(time.time()))))
                    now = time.time()

            except Exception as e:
                print("ERROR - {}".format(str(e)))
                sys.exit()


        print("Orphans: {}".format(orphans))
        print("Size: {}".format(self.sizeof_fmt(size_to_reclaim)))

    def sizeof_fmt(self, num, suffix='B'):
        for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
            if abs(num) < 1024.0:
                return "%3.1f%s%s" % (num, unit, suffix)
            num /= 1024.0
        return "%.1f%s%s" % (num, 'Yi', suffix)