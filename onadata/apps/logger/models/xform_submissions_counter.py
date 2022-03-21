import datetime

from django.contrib.auth.models import User
from django.contrib.gis.db import models
from django.utils import timezone

from onadata.apps.logger.models.xform import XForm


class XFormSubmissionCounter(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    xform = models.ForeignKey(XForm, related_name='xformsubmissioncounter', on_delete=models.CASCADE)
    count = models.IntegerField(default=0)
    timestamp = models.DateField()

    class Meta:
        unique_together = (('user', 'xform', 'timestamp'),)

    def save(self, *args, **kwargs):
        if not self.timestamp:
            today = datetime.date.today()
            first_day_of_month = today.replace(day=1)
            self.timestamp = first_day_of_month

        super().save(*args, **kwargs)
