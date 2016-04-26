from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.reverse import reverse

from onadata.apps.logger.models import XForm
from onadata.libs.permissions import get_object_users_with_permissions
from onadata.libs.serializers.fields.boolean_field import BooleanField
from onadata.libs.serializers.tag_list_serializer import TagListSerializer
from onadata.libs.serializers.metadata_serializer import MetaDataSerializer
from onadata.libs.utils.decorators import check_obj


class XFormSerializer(serializers.HyperlinkedModelSerializer):
    formid = serializers.ReadOnlyField(source='id')
    metadata = serializers.SerializerMethodField('get_xform_metadata')
    owner = serializers.HyperlinkedRelatedField(view_name='user-detail',
                                                source='user',
                                                lookup_field='username',
                                                queryset=User.objects.all())
    public = BooleanField(source='shared')
    public_data = BooleanField(source='shared_data')
    require_auth = BooleanField()
    submission_count_for_today = serializers.ReadOnlyField()
    tags = TagListSerializer(read_only=True)
    title = serializers.CharField(max_length=255)
    url = serializers.HyperlinkedIdentityField(view_name='xform-detail',
                                               lookup_field='pk')
    users = serializers.SerializerMethodField('get_xform_permissions')

    # Tests are expecting this "public" to be passed only "True" or "False"
    # and as a string. I don't know how it worked pre-migrations to django 1.8
    # but now it must be implemented manually
    def validate(self, attrs):
        shared = attrs.get('shared')
        if shared not in (None, 'True', 'False'):
            msg = "'%s' value must be either True or False." % shared
            raise serializers.ValidationError({'shared': msg})
        attrs['shared'] = shared == 'True'
        return attrs

    class Meta:
        model = XForm
        read_only_fields = (
            'json', 'xml', 'date_created', 'date_modified', 'encrypted',
            'bamboo_dataset', 'last_submission_time')
        exclude = ('json', 'xml', 'xls', 'user',
                   'has_start_time', 'shared', 'shared_data')

    # Again, this is to match unit tests
    @property
    def data(self):
        data = super(XFormSerializer, self).data
        if 'num_of_submissions' in data and data['num_of_submissions'] is None:
            data['num_of_submissions'] = 0
        return data

    def get_xform_permissions(self, obj):
        return get_object_users_with_permissions(obj, serializable=True)

    def get_xform_metadata(self, obj):
        if obj:
            return MetaDataSerializer(obj.metadata_set.all(),
                                      many=True, context=self.context).data

        return []


class XFormListSerializer(serializers.Serializer):
    formID = serializers.ReadOnlyField(source='id_string')
    name = serializers.ReadOnlyField(source='title')
    majorMinorVersion = serializers.SerializerMethodField('get_version')
    version = serializers.SerializerMethodField()
    hash = serializers.SerializerMethodField()
    descriptionText = serializers.ReadOnlyField(source='description')
    downloadUrl = serializers.SerializerMethodField('get_url')
    manifestUrl = serializers.SerializerMethodField('get_manifest_url')

    def get_version(self, obj):
        return None

    @check_obj
    def get_hash(self, obj):
        return u"md5:%s" % obj.hash

    @check_obj
    def get_url(self, obj):
        kwargs = {'pk': obj.pk, 'username': obj.user.username}
        request = self.context.get('request')

        return reverse('download_xform', kwargs=kwargs, request=request)

    @check_obj
    def get_manifest_url(self, obj):
        kwargs = {'pk': obj.pk, 'username': obj.user.username}
        request = self.context.get('request')

        return reverse('manifest-url', kwargs=kwargs, request=request)


class XFormManifestSerializer(serializers.Serializer):
    filename = serializers.ReadOnlyField(source='data_value')
    hash = serializers.SerializerMethodField()
    downloadUrl = serializers.SerializerMethodField('get_url')

    @check_obj
    def get_url(self, obj):
        kwargs = {'pk': obj.xform.pk,
                  'username': obj.xform.user.username,
                  'metadata': obj.pk}
        request = self.context.get('request')
        format = obj.data_value[obj.data_value.rindex('.') + 1:]

        return reverse('xform-media', kwargs=kwargs,
                       request=request, format=format.lower())

    @check_obj
    def get_hash(self, obj):
        return u"%s" % (obj.file_hash or 'md5:')
