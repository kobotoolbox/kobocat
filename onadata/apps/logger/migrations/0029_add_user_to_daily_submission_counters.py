from django.conf import settings
from django.db import migrations, models
from django.db.models import Subquery, deletion


def add_user_to_daily_submission_counter(apps, schema_editor):
    DailyXFormSubmissionCounter = apps.get_model("logger", "DailyXFormSubmissionCounter")
    # delete any counters where xform and user are None, since we can't associate them with a user
    DailyXFormSubmissionCounter.objects.filter(xform=None, user=None).delete()
    # add the user to the counter, based on the xform user
    DailyXFormSubmissionCounter.objects.all().exclude(xform=None).update(
        user=Subquery(
            DailyXFormSubmissionCounter.objects.all().exclude(xform=None).values('xform__user')[:1]
        ),
    )


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('logger', '0028_populate_daily_xform_counters_for_year'),
    ]

    operations = [
        migrations.AddField(
            model_name='DailyXFormSubmissionCounter',
            name='user',
            field=models.ForeignKey('auth.User', related_name='daily_users', null=True, on_delete=models.CASCADE),
        ),
        migrations.RunPython(
            add_user_to_daily_submission_counter,
            migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name='dailyxformsubmissioncounter',
            name='xform',
            field=models.ForeignKey(null=True, on_delete=deletion.CASCADE,
                                    related_name='daily_counters', to='logger.xform'),
        ),
        migrations.AlterUniqueTogether(
            name='dailyxformsubmissioncounter',
            unique_together=set(),
        ),
        migrations.AddIndex(
            model_name='dailyxformsubmissioncounter',
            index=models.Index(fields=['date', 'user'], name='logger_dail_date_f738ed_idx'),
        ),
        migrations.AddConstraint(
            model_name='dailyxformsubmissioncounter',
            constraint=models.UniqueConstraint(fields=('date', 'user', 'xform'), name='daily_unique_with_xform'),
        ),
        migrations.AddConstraint(
            model_name='dailyxformsubmissioncounter',
            constraint=models.UniqueConstraint(condition=models.Q(('xform', None)), fields=('date', 'user'),
                                               name='daily_unique_without_xform'),
        ),
    ]
