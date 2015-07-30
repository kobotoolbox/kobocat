from datetime import datetime, date
import json
import os
import re
import six
from urlparse import urlparse
  
from bson import json_util
from django.conf import settings
from django.core.files.base import File
from django.core.files.temp import NamedTemporaryFile
from django.core.files.storage import get_storage_class
from django.contrib.auth.models import User
from django.shortcuts import render_to_response
from json2xlsclient.client import Client

from onadata.apps.logger.models import Attachment, Instance, XForm
from onadata.apps.main.models.meta_data import MetaData
from onadata.apps.viewer.models.export import Export
from onadata.apps.viewer.models.parsed_instance import dict_for_mongo

from onadata.libs.utils.viewer_tools import create_attachments_zipfile
from onadata.libs.utils.common_tags import (
    USERFORM_ID, INDEX, PARENT_INDEX, PARENT_TABLE_NAME, TAGS, NOTES)
from onadata.libs.exceptions import J2XException
from onadata.libs.utils.google_sheets import SheetsExportBuilder
from onadata.libs.utils.csv_export import FlatCsvExportBuilder, ZippedCsvExportBuilder   
from onadata.libs.utils.sav_export import ZippedSavExportBuilder
from onadata.libs.utils.xls_export import XlsExportBuilder
     
# this is Mongo Collection where we will store the parsed submissions
xform_instances = settings.MONGO_DB.instances

QUESTION_TYPES_TO_EXCLUDE = [
    u'note',
]


def question_types_to_exclude(_type):
    return _type in QUESTION_TYPES_TO_EXCLUDE


class DictOrganizer(object):

    def set_dict_iterator(self, dict_iterator):
        self._dict_iterator = dict_iterator

    # Every section will get its own table
    # I need to think of an easy way to flatten out a dictionary
    # parent name, index, table name, data
    def _build_obs_from_dict(self, d, obs, table_name,
                             parent_table_name, parent_index):
        if table_name not in obs:
            obs[table_name] = []
        this_index = len(obs[table_name])
        obs[table_name].append({
            u"_parent_table_name": parent_table_name,
            u"_parent_index": parent_index,
        })
        for k, v in d.items():
            if type(v) != dict and type(v) != list:
                assert k not in obs[table_name][-1]
                obs[table_name][-1][k] = v
        obs[table_name][-1][u"_index"] = this_index

        for k, v in d.items():
            if type(v) == dict:
                kwargs = {
                    "d": v,
                    "obs": obs,
                    "table_name": k,
                    "parent_table_name": table_name,
                    "parent_index": this_index
                }
                self._build_obs_from_dict(**kwargs)
            if type(v) == list:
                for i, item in enumerate(v):
                    kwargs = {
                        "d": item,
                        "obs": obs,
                        "table_name": k,
                        "parent_table_name": table_name,
                        "parent_index": this_index,
                    }
                    self._build_obs_from_dict(**kwargs)
        return obs

    def get_observation_from_dict(self, d):
        result = {}
        assert len(d.keys()) == 1
        root_name = d.keys()[0]
        kwargs = {
            "d": d[root_name],
            "obs": result,
            "table_name": root_name,
            "parent_table_name": u"",
            "parent_index": -1,
        }
        self._build_obs_from_dict(**kwargs)
        return result


def generate_export(export_type, extension, username, id_string,
                    export_id=None, filter_query=None, group_delimiter='/',
                    split_select_multiples=True,
                    binary_select_multiples=False,
                    google_token=None):
    """
    Create appropriate export object given the export type
    """
    # TODO resolve circular import
    from onadata.apps.viewer.models.export import Export
    export_type_class_map = {
        Export.XLS_EXPORT: XlsExportBuilder,
        Export.GSHEETS_EXPORT: SheetsExportBuilder,
        Export.CSV_EXPORT: FlatCsvExportBuilder,
        Export.CSV_ZIP_EXPORT: ZippedCsvExportBuilder,
        Export.SAV_ZIP_EXPORT: ZippedSavExportBuilder,
    }

    xform = XForm.objects.get(
        user__username__iexact=username, id_string__exact=id_string)

    # query mongo for the cursor
    records = query_mongo(username, id_string, filter_query)
    
    export_builder = export_type_class_map[export_type]()
    export_builder.GROUP_DELIMITER = group_delimiter
    export_builder.SPLIT_SELECT_MULTIPLES = split_select_multiples
    export_builder.BINARY_SELECT_MULTIPLES = binary_select_multiples
    export_builder.SHEET_TITLE = "%s_%s" % (
        id_string, datetime.now().strftime("%Y_%m_%d_%H_%M_%S"))
    export_builder.set_survey(xform.data_dictionary().survey)
     
    if extension:
        temp_file = NamedTemporaryFile(suffix=("." + extension))
    else:
        temp_file = NamedTemporaryFile()
        
    # Login to sheets before exporting.
    if export_type == Export.GSHEETS_EXPORT:
        export_builder.login_with_auth_token(google_token)
        
    # run the export
    export_builder.export(
        temp_file.name, records, username, id_string, filter_query)

    # generate filename
    filename = export_builder.SHEET_TITLE
    if extension:
        filename = filename + "." + extension

    # check filename is unique
    while not Export.is_filename_unique(xform, filename):
        filename = increment_index_in_filename(filename)

    file_path = os.path.join(
        username,
        'exports',
        id_string,
        export_type,
        filename)

    # TODO: if s3 storage, make private - how will we protect local storage??
    storage = get_storage_class()()
    # seek to the beginning as required by storage classes
    temp_file.seek(0)
    export_filename = storage.save(
        file_path,
        File(temp_file, file_path))
    temp_file.close()

    dir_name, basename = os.path.split(export_filename)

    # get or create export object
    if export_id:
        export = Export.objects.get(id=export_id)
    else:
        export = Export(xform=xform, export_type=export_type)
    export.filedir = dir_name
    export.filename = basename
    export.internal_status = Export.SUCCESSFUL
    # Get URL of the exported sheet.
    if export_type == Export.GSHEETS_EXPORT:
        export.export_url = export_builder.url
        
    # dont persist exports that have a filter
    if filter_query is None:
        export.save()
    return export


def query_mongo(username, id_string, query=None, hide_deleted=True):
    query = json.loads(query, object_hook=json_util.object_hook)\
        if query else {}
    query = dict_for_mongo(query)
    query[USERFORM_ID] = u'{0}_{1}'.format(username, id_string)
    if hide_deleted:
        # display only active elements
        # join existing query with deleted_at_query on an $and
        query = {"$and": [query, {"_deleted_at": None}]}
    return xform_instances.find(query)


def should_create_new_export(xform, export_type):
    # TODO resolve circular import
    from onadata.apps.viewer.models.export import Export
    if Export.objects.filter(
            xform=xform, export_type=export_type).count() == 0\
            or Export.exports_outdated(xform, export_type=export_type):
        return True
    return False


def newset_export_for(xform, export_type):
    """
    Make sure you check that an export exists before calling this,
    it will a DoesNotExist exception otherwise
    """
    # TODO resolve circular import
    from onadata.apps.viewer.models.export import Export
    return Export.objects.filter(xform=xform, export_type=export_type)\
        .latest('created_on')


def increment_index_in_filename(filename):
    """
    filename should be in the form file.ext or file-2.ext - we check for the
    dash and index and increment appropriately
    """
    # check for an index i.e. dash then number then dot extension
    regex = re.compile(r"(.+?)\-(\d+)(\..+)")
    match = regex.match(filename)
    if match:
        basename = match.groups()[0]
        index = int(match.groups()[1]) + 1
        ext = match.groups()[2]
    else:
        index = 1
        # split filename from ext
        basename, ext = os.path.splitext(filename)
    new_filename = "%s-%d%s" % (basename, index, ext)
    return new_filename


def generate_attachments_zip_export(
        export_type, extension, username, id_string, export_id=None,
        filter_query=None):
    # TODO resolve circular import
    from onadata.apps.viewer.models.export import Export
    xform = XForm.objects.get(user__username=username, id_string=id_string)
    attachments = Attachment.objects.filter(instance__xform=xform)
    basename = "%s_%s" % (id_string,
                          datetime.now().strftime("%Y_%m_%d_%H_%M_%S"))
    filename = basename + "." + extension
    file_path = os.path.join(
        username,
        'exports',
        id_string,
        export_type,
        filename)
    storage = get_storage_class()()
    zip_file = None

    try:
        zip_file = create_attachments_zipfile(attachments)

        try:
            temp_file = open(zip_file.name)
            export_filename = storage.save(
                file_path,
                File(temp_file, file_path))
        finally:
            temp_file.close()
    finally:
        zip_file and zip_file.close()

    dir_name, basename = os.path.split(export_filename)

    # get or create export object
    if(export_id):
        export = Export.objects.get(id=export_id)
    else:
        export = Export.objects.create(xform=xform, export_type=export_type)

    export.filedir = dir_name
    export.filename = basename
    export.internal_status = Export.SUCCESSFUL
    export.save()
    return export


def generate_kml_export(
        export_type, extension, username, id_string, export_id=None,
        filter_query=None):
    # TODO resolve circular import
    from onadata.apps.viewer.models.export import Export
    user = User.objects.get(username=username)
    xform = XForm.objects.get(user__username=username, id_string=id_string)
    response = render_to_response(
        'survey.kml', {'data': kml_export_data(id_string, user)})

    basename = "%s_%s" % (id_string,
                          datetime.now().strftime("%Y_%m_%d_%H_%M_%S"))
    filename = basename + "." + extension
    file_path = os.path.join(
        username,
        'exports',
        id_string,
        export_type,
        filename)

    storage = get_storage_class()()
    temp_file = NamedTemporaryFile(suffix=extension)
    temp_file.write(response.content)
    temp_file.seek(0)
    export_filename = storage.save(
        file_path,
        File(temp_file, file_path))
    temp_file.close()

    dir_name, basename = os.path.split(export_filename)

    # get or create export object
    if(export_id):
        export = Export.objects.get(id=export_id)
    else:
        export = Export.objects.create(xform=xform, export_type=export_type)

    export.filedir = dir_name
    export.filename = basename
    export.internal_status = Export.SUCCESSFUL
    export.save()

    return export


def kml_export_data(id_string, user):
    # TODO resolve circular import
    from onadata.apps.viewer.models.data_dictionary import DataDictionary
    dd = DataDictionary.objects.get(id_string=id_string, user=user)
    instances = Instance.objects.filter(
        xform__user=user,
        xform__id_string=id_string,
        deleted_at=None,
        geom__isnull=False
    ).order_by('id')
    data_for_template = []

    for instance in instances:
        point = instance.point
        if point:
            data_for_template.append({
                'name': id_string,
                'id': instance.uuid,
                'lat': point.y,
                'lng': point.x,
                })


    return data_for_template


def _get_records(instances):
    records = []
    for instance in instances:
        record = instance.get_dict()
        # Get the keys
        for key in record:
            if '/' in key:
                # replace with _
                record[key.replace('/', '_')]\
                    = record.pop(key)
        records.append(record)

    return records


def _get_server_from_metadata(xform, meta, token):
    report_templates = MetaData.external_export(xform)

    if meta:
        try:
            int(meta)
        except ValueError:
            raise Exception(u"Invalid metadata pk {0}".format(meta))

        # Get the external server from the metadata
        result = report_templates.get(pk=meta)
        server = result.external_export_url
        name = result.external_export_name
    elif token:
        server = token
        name = None
    else:
        # Take the latest value in the metadata
        if not report_templates:
            raise Exception(
                u"Could not find the template token: Please upload template.")

        server = report_templates[0].external_export_url
        name = report_templates[0].external_export_name

    return server, name


def generate_external_export(
    export_type, username, id_string, export_id=None,  token=None,
        filter_query=None, meta=None):

    xform = XForm.objects.get(
        user__username__iexact=username, id_string__exact=id_string)
    user = User.objects.get(username=username)

    server, name = _get_server_from_metadata(xform, meta, token)

    # dissect the url
    parsed_url = urlparse(server)

    token = parsed_url.path[5:]

    ser = parsed_url.scheme + '://' + parsed_url.netloc

    records = _get_records(Instance.objects.filter(
        xform__user=user, xform__id_string=id_string))

    status_code = 0
    if records and server:

        try:

            client = Client(ser)
            response = client.xls.create(token, json.dumps(records))

            if hasattr(client.xls.conn, 'last_response'):
                status_code = client.xls.conn.last_response.status_code
        except Exception as e:
            raise J2XException(
                u"J2X client could not generate report. Server -> {0},"
                u" Error-> {1}".format(server, e)
            )
    else:
        if not server:
            raise J2XException(u"External server not set")
        elif not records:
            raise J2XException(
                u"No record to export. Form -> {0}".format(id_string)
            )

    # get or create export object
    if export_id:
        export = Export.objects.get(id=export_id)
    else:
        export = Export.objects.create(xform=xform, export_type=export_type)

    export.export_url = response
    if status_code == 201:
        export.internal_status = Export.SUCCESSFUL
        export.filename = name + '-' + response[5:] if name else response[5:]
        export.export_url = ser + response
    else:
        export.internal_status = Export.FAILED

    export.save()

    return export


def upload_template_for_external_export(server, file_obj):

    try:
        client = Client(server)
        response = client.template.create(template_file=file_obj)

        if hasattr(client.template.conn, 'last_response'):
            status_code = client.template.conn.last_response.status_code
    except Exception as e:
        response = str(e)
        status_code = 500

    return str(status_code) + '|' + response
