# coding: utf-8
from __future__ import unicode_literals, print_function, division, absolute_import

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('viewer', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='export',
            name='internal_status',
            field=models.SmallIntegerField(default=0),
        ),
    ]
