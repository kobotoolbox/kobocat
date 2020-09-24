# coding: utf-8
from __future__ import unicode_literals, print_function, division, absolute_import

from django.db import migrations, models
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('logger', '0005_instance_xml_hash'),
    ]

    operations = [
        migrations.AddField(
            model_name='instance',
            name='validation_status',
            field=jsonfield.fields.JSONField(default=None, null=True),
        ),
    ]
