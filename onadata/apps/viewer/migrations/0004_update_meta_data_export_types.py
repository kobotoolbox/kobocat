# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('viewer', '0003_auto_20171123_1521'),
    ]

    operations = [
        migrations.AlterField(
            model_name='export',
            name='export_type',
            field=models.CharField(default=b'xls', max_length=10, choices=[(b'xls', b'Excel'), (b'csv', b'CSV'), (b'zip', b'ZIP'), (b'kml', b'kml')]),
        ),
    ]
