# coding: utf-8
import json

from django.utils.six import string_types
from rest_framework import serializers


class JsonField(serializers.Field):

    def to_representation(self, value):
        if isinstance(value, string_types):
            return json.loads(value)

        return value

    def to_internal_value(self, value):
        if isinstance(value, string_types):
            return json.loads(value)

        return value

    @classmethod
    def to_json(cls, data):
        if isinstance(data, string_types):
            return json.loads(data)
        return data
