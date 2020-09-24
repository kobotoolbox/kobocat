# coding: utf-8
from __future__ import unicode_literals, print_function, division, absolute_import
from rest_framework import serializers
from rest_framework import exceptions

from onadata.apps.logger.models import Note
from onadata.apps.logger.models.instance import Instance


class NoteSerializer(serializers.ModelSerializer):

    serializers.ModelSerializer()
    instance = serializers.PrimaryKeyRelatedField(queryset=Instance.objects.all())

    class Meta:
        model = Note

    def save(self, user=None):
        # This used to be in note_viewset
        if user:
            if not user.has_perm('change_xform', self.validated_data['instance'].xform):
                msg = "You are not authorized to add/change notes on this form."
                raise exceptions.PermissionDenied(msg)
        return super(NoteSerializer, self).save()
