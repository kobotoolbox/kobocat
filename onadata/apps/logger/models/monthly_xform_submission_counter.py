# coding: utf-8
import datetime
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q
from django.db.models.constraints import UniqueConstraint


class MonthlyXFormSubmissionCounter(models.Model):
    year = models.IntegerField()
    month = models.IntegerField()
    user = models.ForeignKey(User, related_name='users', on_delete=models.DO_NOTHING)
    xform = models.ForeignKey('logger.XForm', null=True, on_delete=models.SET_NULL)
    counter = models.IntegerField(default=0)

    class Meta:
        constraints = [
            UniqueConstraint(fields=['year', 'month', 'user', 'xform'],
                             name='unique_with_xform'),
            UniqueConstraint(fields=['year', 'month', 'user'],
                             condition=Q(xform=None),
                             name='unique_without_xform')
        ]
        indexes = [
            models.Index(fields=('year', 'month', 'user')),
        ]
