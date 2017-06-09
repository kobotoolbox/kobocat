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
            field=models.CharField(default=b'', max_length=64, db_index=True, blank=True),
        ),
    ]
