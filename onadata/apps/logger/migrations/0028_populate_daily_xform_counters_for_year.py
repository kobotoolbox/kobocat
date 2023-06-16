from django.conf import settings
from django.core.management import call_command
from django.db import migrations


def populate_daily_counts_for_year(apps, schema_editor):
    if settings.SKIP_HEAVY_MIGRATIONS:
        print(
            """
            !!! ATTENTION !!!
            If you have existing projects you need to run this management command:

               > python manage.py populate_submission_counters -f --skip_monthly

            Until you do, total usage counts from /api/v2/service_usage and /api/v2/asset_usage will be incorrect
            """
        )
    else:
        print(
            """
            This might take a while. If it is too slow, you may want to re-run the
            migration with SKIP_HEAVY_MIGRATIONS=True and run the following management command:
            
                           > python manage.py populate_submission_counters -f --skip_monthly

            Until you do, total usage counts from /api/v2/service_usage and /api/v2/asset_usage will be incorrect
            """
        )
        call_command('populate_submission_counters', force=True)


class Migration(migrations.Migration):

    dependencies = [
        ('kpi', '0027_on_delete_cascade_monthlyxformsubmissioncounter'),
    ]

    # allow this command to be run backwards

    operations = [
        migrations.RunPython(
            populate_daily_counts_for_year,
            migrations.RunPython.noop,
        ),
    ]
