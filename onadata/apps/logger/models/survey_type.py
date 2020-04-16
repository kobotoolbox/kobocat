# coding: utf-8
from __future__ import unicode_literals, print_function, division, absolute_import

from django.db import models
from django.utils.encoding import python_2_unicode_compatible


@python_2_unicode_compatible
class SurveyType(models.Model):
    slug = models.CharField(max_length=100, unique=True)

    class Meta:
        app_label = 'logger'

    def __str__(self):
        return "SurveyType: %s" % self.slug
