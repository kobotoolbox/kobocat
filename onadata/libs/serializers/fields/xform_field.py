# coding: utf-8
from __future__ import unicode_literals, print_function, division, absolute_import
from rest_framework import serializers
from onadata.apps.logger.models import XForm


class XFormField(serializers.Field):
    def to_representation(self, obj):
        return obj.pk

    def to_internal_value(self, data):
        return XForm.objects.get(pk=data)
