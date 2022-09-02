# coding: utf-8
import datetime

from django.contrib.auth.models import User
from django.db import models

from onadata.apps.logger.models.xform import XForm


class DailyXFormSubmissionCounter(models.Model):
    date = models.DateField()
    xform = models.ForeignKey(
        XForm, related_name='daily_counters', on_delete=models.CASCADE
    )
    counter = models.IntegerField(default=0)

    class Meta:
        unique_together = (('date', 'xform'),)
