# coding: utf-8
from __future__ import unicode_literals, print_function, division, absolute_import

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('logger', '0012_add_asset_uid_to_xform'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ziggyinstance',
            name='reporter',
        ),
        migrations.RemoveField(
            model_name='ziggyinstance',
            name='xform',
        ),
        migrations.RemoveField(
            model_name='xform',
            name='bamboo_dataset',
        ),
        migrations.DeleteModel(
            name='ZiggyInstance',
        ),
    ]
