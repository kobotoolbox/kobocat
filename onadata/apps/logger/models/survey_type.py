# coding: utf-8
from __future__ import unicode_literals, print_function, division, absolute_import

from django.db import models


class SurveyType(models.Model):
    slug = models.CharField(max_length=100, unique=True)

    class Meta:
        app_label = 'logger'

    def __unicode__(self):
        return "SurveyType: %s" % self.slug
