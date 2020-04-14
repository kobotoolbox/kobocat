# coding: utf-8
from __future__ import unicode_literals, print_function, division, absolute_import

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('logger', '0004_increase-length-of-attachment-mimetype-field'),
    ]

    operations = [
        migrations.AddField(
            model_name='instance',
            name='xml_hash',
            field=models.CharField(default=None, max_length=64, null=True, db_index=True),
        ),
    ]
