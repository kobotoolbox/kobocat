# Generated by Django 2.2.14 on 2021-08-11 14:12

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('logger', '0020_auto_20211018_1558'),
    ]

    operations = [
        migrations.AlterField(
            model_name='submissioncounter',
            name='timestamp',
            field=models.DateField(),
        ),
    ]
