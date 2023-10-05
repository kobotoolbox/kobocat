from django.db import migrations
from django.db.models import Sum
from django.db.models import Value, F, DateField
from django.db.models.functions import Cast, Concat
from django.db.models.functions import ExtractYear, ExtractMonth
from django.utils.timezone import now


def populate_missing_monthly_counters(apps, schema_editor):

    DailyXFormSubmissionCounter = apps.get_model('logger', 'DailyXFormSubmissionCounter')  # noqa
    MonthlyXFormSubmissionCounter = apps.get_model('logger', 'MonthlyXFormSubmissionCounter')  # noqa

    first_daily_counter = DailyXFormSubmissionCounter.objects.order_by(
        'date'
    ).first()
    MonthlyXFormSubmissionCounter.objects.annotate(
        date=Cast(
            Concat(
                F('year'), Value('-'), F('month'), Value('-'), 1
            ),
            DateField(),
        )
    ).filter(date__gte=first_daily_counter.date.replace(day=1)).delete()

    records = (
        DailyXFormSubmissionCounter.objects.filter(
            date__range=[first_daily_counter.date.replace(day=1), now().date()]
        )
        .annotate(year=ExtractYear('date'), month=ExtractMonth('date'))
        .values('month', 'year')
        .annotate(total=Sum('counter'))
        .values('user_id', 'xform_id', 'month', 'year', 'total')
    ).order_by('year', 'month', 'user_id')

    # Do not use `ignore_conflicts=True` to ensure all counters are successfully
    # create.
    # TODO use `update_conflicts` with Django 4.2
    MonthlyXFormSubmissionCounter.objects.bulk_create(
        [
            MonthlyXFormSubmissionCounter(
                year=r['year'],
                month=r['month'],
                user_id=r['user_id'],
                xform_id=r['xform_id'],
                counter=r['total'],
            )
            for r in records
        ],
        batch_size=5000
    )


class Migration(migrations.Migration):

    dependencies = [
        ('logger', '0029_populate_daily_xform_counters_for_year'),
    ]

    operations = [
        migrations.RunPython(
            populate_missing_monthly_counters,
            migrations.RunPython.noop,
        ),
    ]
