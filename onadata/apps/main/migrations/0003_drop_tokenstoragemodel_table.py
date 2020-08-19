# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0002_auto_20160205_1915'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='tokenstoragemodel',
            name='id',
        ),
        migrations.DeleteModel(
            name='TokenStorageModel',
        ),
    ]
