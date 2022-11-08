# coding: utf-8
import datetime
from django.contrib.auth.models import User
from django.db import models
from django.db.models import F, Q
from django.db.models.constraints import UniqueConstraint
from django.db.models.signals import post_delete


class MonthlyXFormSubmissionCounter(models.Model):
    year = models.IntegerField()
    month = models.IntegerField()
    user = models.ForeignKey(User, related_name='users', on_delete=models.DO_NOTHING)
    # `xform = NULL` (one per user per month) is used as a catch-all for
    # deleted projects
    xform = models.ForeignKey('logger.XForm', null=True, on_delete=models.CASCADE)
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

    @classmethod
    def update_catch_all_counter_on_delete(cls, sender, instance, **kwargs):
        if instance.counter < 1:
            return

        criteria = dict(
            year=instance.year,
            month=instance.month,
            user=instance.user,
            xform=None,
        )
        # make sure an instance exists with `xform = NULL`
        cls.objects.get_or_create(**criteria)
        # add the count for the project being deleted to the null-xform
        # instance, atomically!
        cls.objects.filter(**criteria).update(
            counter=F('counter') + instance.counter
        )


# signals are fired during cascade deletion (i.e. deletion initiated by the
# removal of a related object), whereas the `delete()` model method is not
# called
post_delete.connect(
    MonthlyXFormSubmissionCounter.update_catch_all_counter_on_delete,
    sender=MonthlyXFormSubmissionCounter,
    dispatch_uid='update_catch_all_monthly_xform_submission_counter',
)
