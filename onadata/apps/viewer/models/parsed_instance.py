import datetime
import json
import logging

from bson import json_util, ObjectId
from celery import task
from dateutil import parser
from django.conf import settings
from django.db import models
from django.db.models.signals import post_save, pre_delete
from django.utils.translation import ugettext as _

from onadata.apps.logger.models import Instance
from onadata.apps.logger.models import Note
from onadata.apps.restservice.utils import call_service
from onadata.libs.utils.common_tags import ID, UUID, ATTACHMENTS, GEOLOCATION,\
    SUBMISSION_TIME, MONGO_STRFTIME, BAMBOO_DATASET_ID, DELETEDAT, TAGS,\
    NOTES, SUBMITTED_BY, VALIDATION_STATUS
from onadata.libs.utils.decorators import apply_form_field_names
from onadata.libs.utils.model_tools import queryset_iterator
from onadata.apps.api.mongo_helper import MongoHelper


# this is Mongo Collection where we will store the parsed submissions
xform_instances = settings.MONGO_DB.instances
DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S'


class ParseError(Exception):
    pass


def datetime_from_str(text):
    # Assumes text looks like 2011-01-01T09:50:06.966
    if text is None:
        return None
    dt = None
    try:
        dt = parser.parse(text)
    except Exception:
        return None
    return dt

@task
def update_mongo_instance(record):
    # since our dict always has an id, save will always result in an upsert op
    # - so we dont need to worry whether its an edit or not
    # http://api.mongodb.org/python/current/api/pymongo/collection.html#pymong\
    # o.collection.Collection.save
    try:
        return xform_instances.save(record)
    except Exception:
        logging.getLogger().warning('Submission could not be saved to Mongo.', exc_info=True)
        pass


class ParsedInstance(models.Model):
    USERFORM_ID = u'_userform_id'
    STATUS = u'_status'
    DEFAULT_LIMIT = 30000
    DEFAULT_BATCHSIZE = 1000

    instance = models.OneToOneField(Instance, related_name="parsed_instance")
    start_time = models.DateTimeField(null=True)
    end_time = models.DateTimeField(null=True)
    # TODO: decide if decimal field is better than float field.
    lat = models.FloatField(null=True)
    lng = models.FloatField(null=True)

    class Meta:
        app_label = "viewer"

    @classmethod
    @apply_form_field_names
    def query_mongo(cls, username, id_string, query, fields, sort, start=0,
                    limit=DEFAULT_LIMIT, count=False, hide_deleted=True):

        cursor = cls._get_mongo_cursor(query, fields, hide_deleted, username, id_string)

        if count:
            return [{"count": cursor.count()}]

        if isinstance(sort, basestring):
            sort = json.loads(sort, object_hook=json_util.object_hook)
        sort = sort if sort else {}

        if start < 0 or limit < 0:
            raise ValueError(_("Invalid start/limit params"))

        return cls._get_paginated_and_sorted_cursor(cursor, start, limit, sort)

    @classmethod
    @apply_form_field_names
    def mongo_aggregate(cls, query, pipeline, hide_deleted=True):
        """Perform mongo aggregate queries
        query - is a dict which is to be passed to $match, a pipeline operator
        pipeline - list of dicts or dict of mongodb pipeline operators,
        http://docs.mongodb.org/manual/reference/operator/aggregation-pipeline
        """
        if isinstance(query, basestring):
            query = json.loads(
                query, object_hook=json_util.object_hook) if query else {}
        if not (isinstance(pipeline, dict) or isinstance(pipeline, list)):
            raise Exception(_(u"Invalid pipeline! %s" % pipeline))
        if not isinstance(query, dict):
            raise Exception(_(u"Invalid query! %s" % query))
        query = MongoHelper.to_safe_dict(query)
        if hide_deleted:
            # display only active elements
            deleted_at_query = {
                "$or": [{"_deleted_at": {"$exists": False}},
                        {"_deleted_at": None}]}
            # join existing query with deleted_at_query on an $and
            query = {"$and": [query, deleted_at_query]}
        k = [{'$match': query}]
        if isinstance(pipeline, list):
            k.extend(pipeline)
        else:
            k.append(pipeline)
        results = xform_instances.aggregate(k)
        return results['result']

    @classmethod
    @apply_form_field_names
    def query_mongo_minimal(
            cls, query, fields, sort, start=0, limit=DEFAULT_LIMIT,
            count=False, hide_deleted=True):

        cursor = cls._get_mongo_cursor(query, fields, hide_deleted)

        if count:
            return [{"count": cursor.count()}]

        if isinstance(sort, basestring):
            sort = json.loads(sort, object_hook=json_util.object_hook)
        sort = sort if sort else {}

        if start < 0 or limit < 0:
            raise ValueError(_("Invalid start/limit params"))

        if limit > cls.DEFAULT_LIMIT:
            limit = cls.DEFAULT_LIMIT

        return cls._get_paginated_and_sorted_cursor(cursor, start, limit, sort)

    @classmethod
    @apply_form_field_names
    def query_mongo_no_paging(cls, query, fields, count=False, hide_deleted=True):

        cursor = cls._get_mongo_cursor(query, fields, hide_deleted)

        if count:
            return [{"count": cursor.count()}]
        else:
            return cursor

    @classmethod
    def _get_mongo_cursor(cls, query, fields, hide_deleted, username=None, id_string=None):
        """
        Returns a Mongo cursor based on the query.

        :param query: JSON string
        :param fields: Array string
        :param hide_deleted: boolean
        :param username: string
        :param id_string: string
        :return: pymongo Cursor
        """
        fields_to_select = {cls.USERFORM_ID: 0}
        # TODO: give more detailed error messages to 3rd parties
        # using the API when json.loads fails
        if isinstance(query, basestring):
            query = json.loads(query, object_hook=json_util.object_hook)
        query = query if query else {}
        query = MongoHelper.to_safe_dict(query, reading=True)

        if username and id_string:
            query[cls.USERFORM_ID] = u'%s_%s' % (username, id_string)
            # check if query contains and _id and if its a valid ObjectID
            if '_uuid' in query and ObjectId.is_valid(query['_uuid']):
                query['_uuid'] = ObjectId(query['_uuid'])

        if hide_deleted:
            # display only active elements
            # join existing query with deleted_at_query on an $and
            query = {"$and": [query, {"_deleted_at": None}]}

        # fields must be a string array i.e. '["name", "age"]'
        if isinstance(fields, basestring):
            fields = json.loads(fields, object_hook=json_util.object_hook)
        fields = fields if fields else []

        # TODO: current mongo (2.0.4 of this writing)
        # cant mix including and excluding fields in a single query
        if type(fields) == list and len(fields) > 0:
            fields_to_select = dict(
                [(MongoHelper.encode(field), 1) for field in fields])

        return xform_instances.find(query, fields_to_select)

    @classmethod
    def _get_paginated_and_sorted_cursor(cls, cursor, start, limit, sort):
        """
        Applies pagination and sorting on mongo cursor.

        :param mongo_cursor: pymongo.cursor.Cursor
        :param start: integer
        :param limit: integer
        :param sort: dict
        :return: pymongo.cursor.Cursor
        """
        cursor.skip(start).limit(limit)

        if type(sort) == dict and len(sort) == 1:
            sort = MongoHelper.to_safe_dict(sort, reading=True)
            sort_key = sort.keys()[0]
            sort_dir = int(sort[sort_key])  # -1 for desc, 1 for asc
            cursor.sort(sort_key, sort_dir)

        # set batch size
        cursor.batch_size = cls.DEFAULT_BATCHSIZE
        return cursor

    def to_dict_for_mongo(self):
        d = self.to_dict()
        data = {
            UUID: self.instance.uuid,
            ID: self.instance.id,
            BAMBOO_DATASET_ID: self.instance.xform.bamboo_dataset,
            self.USERFORM_ID: u'%s_%s' % (
                self.instance.xform.user.username,
                self.instance.xform.id_string),
            ATTACHMENTS: _get_attachments_from_instance(self.instance),
            self.STATUS: self.instance.status,
            GEOLOCATION: [self.lat, self.lng],
            SUBMISSION_TIME: self.instance.date_created.strftime(
                MONGO_STRFTIME),
            TAGS: list(self.instance.tags.names()),
            NOTES: self.get_notes(),
            VALIDATION_STATUS: self.instance.get_validation_status(),
            SUBMITTED_BY: self.instance.user.username
            if self.instance.user else None
        }

        if isinstance(self.instance.deleted_at, datetime.datetime):
            data[DELETEDAT] = self.instance.deleted_at.strftime(MONGO_STRFTIME)

        d.update(data)

        return MongoHelper.to_safe_dict(d)

    def update_mongo(self, async=True):
        d = self.to_dict_for_mongo()
        if d.get("_xform_id_string") is None:
            # if _xform_id_string, Instance could not be parsed.
            # so, we don't update mongo.
            return False
        else:
            if async:
                update_mongo_instance.apply_async((), {"record": d})
            else:
                update_mongo_instance(d)
        return True

    @staticmethod
    def bulk_update_validation_statuses(query, validation_status):
        return xform_instances.update(query, {"$set":
            {VALIDATION_STATUS: validation_status}}, multi=True)

    def to_dict(self):
        if not hasattr(self, "_dict_cache"):
            self._dict_cache = self.instance.get_dict()
        return self._dict_cache

    @classmethod
    def dicts(cls, xform):
        qs = cls.objects.filter(instance__xform=xform)
        for parsed_instance in queryset_iterator(qs):
            yield parsed_instance.to_dict()

    def _get_name_for_type(self, type_value):
        """
        We cannot assume that start time and end times always use the same
        XPath. This is causing problems for other peoples' forms.

        This is a quick fix to determine from the original XLSForm's JSON
        representation what the 'name' was for a given
        type_value ('start' or 'end')
        """
        datadict = json.loads(self.instance.xform.json)
        for item in datadict['children']:
            if type(item) == dict and item.get(u'type') == type_value:
                return item['name']

    def get_data_dictionary(self):
        # TODO: fix hack to get around a circular import
        from onadata.apps.viewer.models.data_dictionary import\
            DataDictionary
        return DataDictionary.objects.get(
            user=self.instance.xform.user,
            id_string=self.instance.xform.id_string
        )

    data_dictionary = property(get_data_dictionary)

    # TODO: figure out how much of this code should be here versus
    # data_dictionary.py.
    def _set_geopoint(self):
        if self.instance.point:
            self.lat = self.instance.point.y
            self.lng = self.instance.point.x

    def save(self, async=False, *args, **kwargs):
        # start/end_time obsolete: originally used to approximate for
        # instanceID, before instanceIDs were implemented
        self.start_time = None
        self.end_time = None
        self._set_geopoint()
        super(ParsedInstance, self).save(*args, **kwargs)
        # insert into Mongo
        return self.update_mongo(async)

    def add_note(self, note):
        note = Note(instance=self.instance, note=note)
        note.save()

    def remove_note(self, pk):
        note = self.instance.notes.get(pk=pk)
        note.delete()

    def get_notes(self):
        notes = []
        note_qs = self.instance.notes.values(
            'id', 'note', 'date_created', 'date_modified')
        for note in note_qs:
            note['date_created'] = \
                note['date_created'].strftime(MONGO_STRFTIME)
            note['date_modified'] = \
                note['date_modified'].strftime(MONGO_STRFTIME)
            notes.append(note)
        return notes


def _get_attachments_from_instance(instance):
    attachments = []
    for a in instance.attachments.all():
        attachment = dict()
        attachment['download_url'] = a.media_file.url
        attachment['mimetype'] = a.mimetype
        attachment['filename'] = a.media_file.name
        attachment['instance'] = a.instance.pk
        attachment['xform'] = instance.xform.id
        attachment['id'] = a.id
        attachments.append(attachment)

    return attachments


def _remove_from_mongo(sender, **kwargs):
    instance_id = kwargs.get('instance').instance.id
    xform_instances.remove(instance_id)

pre_delete.connect(_remove_from_mongo, sender=ParsedInstance)


def rest_service_form_submission(sender, **kwargs):
    parsed_instance = kwargs.get('instance')
    created = kwargs.get('created')
    if created:
        call_service(parsed_instance)


post_save.connect(rest_service_form_submission, sender=ParsedInstance)
