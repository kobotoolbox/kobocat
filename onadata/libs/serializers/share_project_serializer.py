from django.core.validators import ValidationError
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _

from rest_framework import serializers
from onadata.libs.models.share_project import ShareProject
from onadata.libs.permissions import ROLES
from onadata.libs.serializers.fields.project_field import ProjectField


class ShareProjectSerializer(serializers.Serializer):
    project = ProjectField()
    username = serializers.CharField(max_length=255)
    role = serializers.CharField(max_length=50)

    def update(self, instance, validated_data):
        instance.project = validated_data.get('project', instance.project)
        instance.username = validated_data.get('username', instance.username)
        instance.role = validated_data.get('role', instance.role)
        return instance

    def create(self, validated_data):
        project = ShareProject(**validated_data)
        project.save()
        return project

    def validate_username(self, value):
        """Check that the username exists"""
        try:
            User.objects.get(username=value)
        except User.DoesNotExist:
            raise ValidationError(_(u"User '%(value)s' does not exist."
                                    % {"value": value}))

        return value

    def validate_role(self, value):
        """check that the role exists"""

        if value not in ROLES:
            raise ValidationError(_(u"Unknown role '%(role)s'."
                                    % {"role": value}))

        return value

    def remove_user(self):
        obj = ShareProject(**self.validated_data)
        obj.remove_user()
