# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('viewer', '0002_auto_20160205_1915'),
    ]

    operations = [
        migrations.AlterField(
            model_name='export',
            name='export_type',
            field=models.CharField(default=b'xls', max_length=10, choices=[(b'xls', b'Excel'), (b'csv', b'CSV'), (b'gdoc', b'GDOC'), (b'zip', b'ZIP'), (b'kml', b'kml'), (b'csv_zip', b'CSV ZIP'), (b'sav_zip', b'SAV ZIP'), (b'sav', b'SAV'), (b'external', b'Excel'), (b'analyser', b'Analyser')]),
        ),
    ]
