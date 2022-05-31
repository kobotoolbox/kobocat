# coding: utf-8
from django.core.validators import ValidationError
from django.contrib.auth.models import User
from django.utils.translation import gettext as t

from rest_framework import serializers
from onadata.libs.models.clone_xform import CloneXForm
from onadata.libs.serializers.fields.xform_field import XFormField


class CloneXFormSerializer(serializers.Serializer):

    xform = XFormField()
    username = serializers.CharField(max_length=255)

    class Meta:
        fields = '__all__'

    def create(self, validated_data):
        obj = CloneXForm(**validated_data)
        obj.save()
        return obj

    def update(self, instance, validated_data):
        instance.xform = validated_data.get('xform', instance.xform)
        instance.username = validated_data.get('username', instance.username)
        return instance

    def validate_username(self, value):
        """Check that the username exists"""
        try:
            User.objects.get(username=value)
        except User.DoesNotExist:
            raise ValidationError(t("User '%(value)s' does not exist."
                                    % {"value": value}))

        return value
