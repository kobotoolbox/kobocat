# coding: utf-8
from __future__ import unicode_literals, print_function, division, absolute_import

from django.db import migrations, models
import onadata.apps.logger.fields


class Migration(migrations.Migration):

    dependencies = [
        ('logger', '0008_add_instance_is_synced_with_mongo_and_xform_has_kpi_hooks'),
    ]

    operations = [
        migrations.AddField(
            model_name='instance',
            name='posted_to_kpi',
            field=onadata.apps.logger.fields.LazyDefaultBooleanField(default=False),
        ),
    ]
