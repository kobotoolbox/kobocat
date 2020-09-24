# coding: utf-8
from __future__ import unicode_literals, print_function, division, absolute_import
from rest_framework import serializers
import json


class JsonField(serializers.Field):

    def to_representation(self, value):
        if isinstance(value, basestring):
            return json.loads(value)

        return value

    def to_internal_value(self, value):
        if isinstance(value, basestring):
            return json.loads(value)

        return value

    @classmethod
    def to_json(cls, data):
        if isinstance(data, basestring):
            return json.loads(data)
        return data
