# coding: utf-8
import datetime
from django.contrib.auth.models import User
from django.contrib.gis.db import models


class SubmissionCounter(models.Model):
    user = models.ForeignKey(
        User,
        related_name='submissioncounter',
        null=True,
        on_delete=models.CASCADE,
    )
    count = models.IntegerField(default=0)
    timestamp = models.DateField()

    class Meta:
        unique_together = (('user', 'timestamp'),)

    def save(self, *args, **kwargs):
        if not self.timestamp:
            today = datetime.date.today()
            first_day_of_month = today.replace(day=1)
            self.timestamp = first_day_of_month

        super().save(*args, **kwargs) 
