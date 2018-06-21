# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import onadata.apps.logger.fields


class Migration(migrations.Migration):

    dependencies = [
        ('logger', '0007_add_validate_permission_on_xform'),
    ]

    operations = [
        migrations.AddField(
            model_name='instance',
            name='mongo_success',
            field=onadata.apps.logger.fields.LazyDefaultBooleanField(default=False),
        ),
        migrations.AddField(
            model_name='xform',
            name='has_kpi_hooks',
            field=onadata.apps.logger.fields.LazyDefaultBooleanField(default=False),
        ),
    ]
