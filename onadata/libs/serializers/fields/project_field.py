from rest_framework import serializers
from onadata.apps.api.models.project import Project


class ProjectField(serializers.Field):
    def to_representation(self, obj):
        return obj.pk

    def to_internal_value(self, data):
        return Project.objects.get(pk=data)
