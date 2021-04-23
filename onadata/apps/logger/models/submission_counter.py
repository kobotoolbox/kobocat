import datetime
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.gis.db import models

class SubmissionCounter(models.Model):
    user = models.ForeignKey(User, related_name='submissioncounter', null=True, on_delete=models.CASCADE)
    count = models.IntegerField(default=0)
    timestamp = models.DateTimeField()

    def save(self, *args, **kwargs):
        today = datetime.date.today()
        first_day_of_month = today.replace(day=1)

        self.timestamp = first_day_of_month
        super().save(*args, **kwargs) 