# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('logger', '0004_auto_20170920_1406'),
    ]

    operations = [
        migrations.AddField(
            model_name='backupxform',
            name='id_string',
            field=models.CharField(default=' ', max_length=100),
            preserve_default=False,
        ),
    ]
