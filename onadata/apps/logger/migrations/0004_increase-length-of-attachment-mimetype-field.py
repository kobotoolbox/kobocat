# coding: utf-8
from __future__ import unicode_literals, print_function, division, absolute_import

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('logger', '0003_add-index-on-attachment-media-file'),
    ]

    operations = [
        migrations.AlterField(
            model_name='attachment',
            name='mimetype',
            field=models.CharField(default=b'', max_length=100, blank=True),
        ),
    ]
