from django.core.validators import ValidationError
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _

from rest_framework import serializers
from onadata.libs.models.share_xform import ShareXForm
from onadata.libs.permissions import ROLES
from onadata.libs.serializers.fields.xform_field import XFormField


class ShareXFormSerializer(serializers.Serializer):
    xform = XFormField()
    username = serializers.CharField(max_length=255)
    role = serializers.CharField(max_length=50)

    def create(self, validated_data):
        return ShareXForm(**validated_data)

    def update(self, instance, validated_data):
        instance.xform = validated_data.get('xform', instance.xform)
        instance.username = validated_data.get('username', instance.username)
        instance.role = validated_data.get('role', instance.role)
        return instance

    def validate_username(self, attrs, source):
        """Check that the username exists"""
        value = attrs[source]
        try:
            User.objects.get(username=value)
        except User.DoesNotExist:
            raise ValidationError(_(u"User '%(value)s' does not exist."
                                    % {"value": value}))

        return attrs

    def validate_role(self, attrs, source):
        """check that the role exists"""
        value = attrs[source]

        if value not in ROLES:
            raise ValidationError(_(u"Unknown role '%(role)s'."
                                    % {"role": value}))

        return attrs
