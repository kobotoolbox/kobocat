# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('logger', '0006_auto_20171021_0941'),
    ]

    operations = [
        migrations.RenameField(
            model_name='backupxform',
            old_name='migration_changes',
            new_name='_migration_changes',
        ),
    ]
