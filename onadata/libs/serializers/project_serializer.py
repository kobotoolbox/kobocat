from django.forms import widgets
from django.contrib.auth.models import User
from rest_framework import serializers

from onadata.apps.api.models import Project
from onadata.apps.logger.models import Instance
from onadata.libs.permissions import get_object_users_with_permissions
from onadata.libs.serializers.fields.boolean_field import BooleanField
from onadata.libs.serializers.fields.json_field import JsonField
from onadata.libs.serializers.tag_list_serializer import TagListSerializer
from onadata.libs.utils.decorators import check_obj


class ProjectSerializer(serializers.HyperlinkedModelSerializer):
    projectid = serializers.ReadOnlyField(source='id')
    url = serializers.HyperlinkedIdentityField(
        view_name='project-detail', lookup_field='pk')
    owner = serializers.HyperlinkedRelatedField(
        view_name='user-detail',
        source='organization',
        lookup_field='username',
        queryset=User.objects.all())
    created_by = serializers.HyperlinkedRelatedField(
        view_name='user-detail',
        lookup_field='username',
        read_only=True)
    metadata = JsonField(required=False)
    starred = serializers.SerializerMethodField('is_starred_project')
    users = serializers.SerializerMethodField('get_project_permissions')
    forms = serializers.SerializerMethodField('get_project_forms')
    public = BooleanField(source='shared')
    tags = TagListSerializer(read_only=True)
    num_datasets = serializers.SerializerMethodField()
    last_submission_date = serializers.SerializerMethodField()

    class Meta:
        model = Project
        exclude = ('organization', 'user_stars')

    def update(self, instance, validated_data):
        metadata = JsonField.to_json(validated_data.get('metadata'))

        if self.partial and metadata:
            if not isinstance(instance.metadata, dict):
                instance.metadata = {}

            instance.metadata.update(metadata)
            validated_data['metadata'] = instance.metadata

        return super(ProjectSerializer, self).update(instance, validated_data)

    def create(self, validated_data):
        if 'request' in self.context:
            created_by = self.context['request'].user

            return Project.objects.create(
                name=validated_data.get('name'),
                organization=validated_data.get('organization'),
                created_by=created_by,
                metadata=validated_data.get('metadata'),)


    def get_project_permissions(self, obj):
        return get_object_users_with_permissions(obj, serializable=True)

    @check_obj
    def get_project_forms(self, obj):
        xforms_details = obj.projectxform_set.values(
            'xform__pk', 'xform__title')
        return [{'name': form['xform__title'], 'id':form['xform__pk']}
                for form in xforms_details]

    @check_obj
    def get_num_datasets(self, obj):
        """Return the number of datasets attached to the object.

        :param obj: The project to find datasets for.
        """
        return obj.projectxform_set.count()

    @check_obj
    def get_last_submission_date(self, obj):
        """Return the most recent submission date to any of the projects
        datasets.

        :param obj: The project to find the last submission date for.
        """
        xform_ids = obj.projectxform_set.values_list('xform', flat=True)
        last_submission = Instance.objects.\
            order_by('-date_created').\
            filter(xform_id__in=xform_ids).values_list('date_created',
                                                       flat=True)

        # Force explicit serialization to a list as it used to rely on
        # an implicit one.
        last_submission = list(last_submission)
        return last_submission and last_submission[0]

    def is_starred_project(self, obj):
        request = self.context['request']
        user = request.user
        user_stars = obj.user_stars.all()
        if user in user_stars:
            return True

        return False
