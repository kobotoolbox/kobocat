# coding: utf-8
from __future__ import unicode_literals, print_function, division, absolute_import
from rest_framework import serializers
from rest_framework.exceptions import ParseError


class TagListSerializer(serializers.Field):

    def to_internal_value(self, data):
        if type(data) is not list:
            raise ParseError("expected a list of data")

        return data

    def to_representation(self, obj):
        if obj is None:
            return super(TagListSerializer, self).to_representation(obj)

        if type(obj) is not list:
            return list(obj.values_list('name', flat=True))

        return obj
