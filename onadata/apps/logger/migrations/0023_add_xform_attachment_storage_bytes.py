# Generated by Django 2.2.28 on 2022-05-17 14:13

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('logger', '0022_misc_model_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='xform',
            name='attachment_storage_bytes',
            field=models.BigIntegerField(default=0),
        ),
    ]
