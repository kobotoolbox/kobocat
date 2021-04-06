import datetime
from django.contrib.auth.models import User
from django.contrib.gis.db import models

class SubmissionCounter(models.Model):
    user = models.ForeignKey(User, related_name='submissioncounter', null=True, on_delete=models.CASCADE)
    count = models.IntegerField(default=0)
    timestamp = models.DateTimeField(auto_now_add=True, blank=True)

    @property
    def month(self):
        return self.timestamp.strftime('%m')
    
    @property
    def year(self):
        return self.timestamp.strftime('%Y')