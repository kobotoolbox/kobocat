from django.contrib.auth.models import User
from rest_framework import serializers

from onadata.libs.serializers.fields.hyperlinked_multi_identity_field import\
    HyperlinkedMultiIdentityField
from onadata.libs.serializers.user_serializer import UserSerializer
from onadata.apps.api.models import OrganizationProfile, Team


class TeamSerializer(serializers.Serializer):
    url = HyperlinkedMultiIdentityField(
        view_name='team-detail')
    name = serializers.CharField(max_length=100, source='team_name',
                                 required=True)
    organization = serializers.SlugRelatedField(
        slug_field='username',
        queryset=User.objects.filter(
            pk__in=OrganizationProfile.objects.values('user')))
    projects = serializers.HyperlinkedRelatedField(view_name='project-detail',
                                                   many=True,
                                                   read_only=True)
    users = serializers.SerializerMethodField('get_team_users')

    def get_team_users(self, obj):
        users = []
        if obj:
            for user in obj.user_set.all():
                # HACK: removing the URL right now because a test does not
                # expect it. We should rather unify the entire API in the
                # future but righ now we need to stick we the tests, which
                # are the closest thing we got to a specification.
                user_data = UserSerializer(instance=user,
                                            context=self.context).data
                user_data.pop('url', None)
                users.append(user_data)

        return users

    def create(self, validated_data):
        org = validated_data.get('organization', None)
        team_name = validated_data.get('team_name', None)
        request = self.context.get('request')
        created_by = request.user

        return Team.objects.create(organization=org, name=team_name,
                                   created_by=created_by)

    def update(self, attrs, instance=None):
        org = attrs.get('organization', None)
        projects = attrs.get('projects', [])

        instance.organization = org if org else instance.organization
        instance.name = attrs.get('team_name', instance.name)
        instance.projects.clear()

        for project in projects:
            instance.projects.add(project)

        return instance
