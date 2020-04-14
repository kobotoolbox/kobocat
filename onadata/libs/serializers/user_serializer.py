# coding: utf-8
from __future__ import unicode_literals, print_function, division, absolute_import
from django.contrib.auth.models import User
from rest_framework import serializers


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'url')
        extra_kwargs = {
            'url': {'lookup_field': 'username'}
        }
