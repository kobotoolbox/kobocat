from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('logger', '0030_backfill_lost_monthly_counters'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dailyxformsubmissioncounter',
            name='user',
            field=models.ForeignKey('auth.User', related_name='daily_users', null=False, on_delete=models.CASCADE),
        ),
    ]
