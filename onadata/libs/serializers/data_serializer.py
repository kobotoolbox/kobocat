import json

from django.utils.translation import ugettext as _
from rest_framework import serializers
from rest_framework.exceptions import ParseError

from onadata.apps.logger.models.xform import XForm
from onadata.apps.viewer.models.parsed_instance import ParsedInstance


class DataSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='data-list', lookup_field='pk')

    class Meta:
        model = XForm
        fields = ('id', 'id_string', 'title', 'description', 'url')
        lookup_field = 'pk'


class DataListSerializer(serializers.Serializer):

    @property
    def data(self):
        if self._data is None:
            obj = self.object

            if self.many:
                self._data = []
                for item in obj:
                    self._data.extend(self.to_representation(item))
            else:
                self._data = self.to_representation(obj)

        return self._data

    def to_representation(self, obj):
        request = self.context.get('request')

        if not hasattr(obj, 'xform') and not isinstance(obj, XForm):
            return super(DataListSerializer, self).to_representation(obj)

        query_params = (request and request.query_params) or {}
        query = {
            ParsedInstance.USERFORM_ID:
            u'%s_%s' % (obj.user.username, obj.id_string)
        }

        try:
            query.update(json.loads(query_params.get('query', '{}')))
        except ValueError:
            raise ParseError(_("Invalid query: %(query)s"
                             % {'query': query_params.get('query')}))

        query_kwargs = {
            'query': json.dumps(query),
            'fields': query_params.get('fields'),
            'sort': query_params.get('sort')
        }
        cursor = ParsedInstance.query_mongo_minimal(**query_kwargs)
        return list(cursor)


class DataInstanceSerializer(serializers.Serializer):
    def to_representation(self, obj):
        if not hasattr(obj, 'xform'):
            return super(DataInstanceSerializer, self).to_representation(obj)

        request = self.context.get('request')
        query_params = (request and request.query_params) or {}
        query = {
            ParsedInstance.USERFORM_ID:
            u'%s_%s' % (obj.xform.user.username, obj.xform.id_string),
            u'_id': obj.pk
        }
        query_kwargs = {
            'query': json.dumps(query),
            'fields': query_params.get('fields'),
            'sort': query_params.get('sort')
        }
        cursor = ParsedInstance.query_mongo_minimal(**query_kwargs)
        records = list(record for record in cursor)

        return (len(records) and records[0]) or records


class SubmissionSerializer(serializers.Serializer):
    def to_representation(self, obj):
        if not hasattr(obj, 'xform'):
            return super(SubmissionSerializer, self).to_representation(obj)

        return {
            'message': _("Successful submission."),
            'formid': obj.xform.id_string,
            'encrypted': obj.xform.encrypted,
            'instanceID': u'uuid:%s' % obj.uuid,
            'submissionDate': obj.date_created.isoformat(),
            'markedAsCompleteDate': obj.date_modified.isoformat()
        }
