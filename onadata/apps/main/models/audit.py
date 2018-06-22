from datetime import datetime, timedelta

from django.conf import settings

from onadata.apps.viewer.models.parsed_instance import DATETIME_FORMAT
from onadata.apps.api.mongo_helper import MongoHelper

audit = settings.MONGO_DB.auditlog
DEFAULT_LIMIT = 1000


class AuditLog(object):
    ACCOUNT = u"account"
    DEFAULT_BATCHSIZE = 1000
    CREATED_ON = u"created_on"

    def __init__(self, data):
        self.data = data

    def save(self):
        return audit.save(self.data)

    @classmethod
    def query_mongo(cls, username, query=None, fields=None, sort=None, start=0,
                    limit=DEFAULT_LIMIT, count=False):
        query = MongoHelper.to_safe_dict(query) if query else {}
        query[cls.ACCOUNT] = username
        # TODO find better method
        # check for the created_on key in query and turn its values into dates
        if type(query) == dict and cls.CREATED_ON in query:
            if type(query[cls.CREATED_ON]) is dict:
                for op, val in query[cls.CREATED_ON].iteritems():
                    try:
                        query[cls.CREATED_ON][op] = datetime.strptime(
                            val, DATETIME_FORMAT)
                    except ValueError:
                        pass
            elif isinstance(query[cls.CREATED_ON], basestring):
                val = query[cls.CREATED_ON]
                try:
                    created_on = datetime.strptime(val, DATETIME_FORMAT)
                except ValueError:
                    pass
                else:
                    # create start and end times for the entire day
                    start_time = created_on.replace(hour=0, minute=0,
                                                    second=0, microsecond=0)
                    end_time = start_time + timedelta(days=1)
                    query[cls.CREATED_ON] = {"$gte": start_time,
                                             "$lte": end_time}

        # TODO: current mongo (2.0.4 of this writing)
        # cant mix including and excluding fields in a single query
        fields_to_select = None
        if type(fields) == list and len(fields) > 0:
            fields_to_select = dict([(MongoHelper.encode(field), 1)
                                     for field in fields])
        cursor = audit.find(query, fields_to_select)
        if count:
            return [{"count": cursor.count()}]

        cursor.skip(max(start, 0)).limit(limit)
        if type(sort) == dict and len(sort) == 1:
            sort = MongoHelper.to_safe_dict(sort, reading=True)
            sort_key = sort.keys()[0]
            sort_dir = int(sort[sort_key])  # -1 for desc, 1 for asc
            cursor.sort(sort_key, sort_dir)
        # set batch size for cursor iteration
        cursor.batch_size = cls.DEFAULT_BATCHSIZE
        return cursor
