# Generated by Django 3.2.15 on 2022-08-30 19:18

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0004_onetimeauthtoken_request_identifier'),
    ]

    operations = [
        migrations.DeleteModel(
            name='OneTimeAuthToken',
        ),
    ]
