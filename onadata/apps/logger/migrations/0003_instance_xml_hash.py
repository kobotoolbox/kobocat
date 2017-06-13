# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('logger', '0002_attachment_filename_length'),
    ]

    operations = [
        migrations.AddField(
            model_name='instance',
            name='xml_hash',
            field=models.CharField(default=None, max_length=64, null=True, db_index=True),
        ),
    ]
