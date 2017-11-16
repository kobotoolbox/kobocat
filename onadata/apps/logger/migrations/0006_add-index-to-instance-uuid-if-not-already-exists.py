# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('logger', '0005_instance_xml_hash'),
    ]

    # This custom migration must be run on Postgres 9.5+.
    # Because some servers already have these modifications applied by Django South migration,
    # we need to use the same indexes names to avoid create duplicate indexes.
    # see onadata/apps/logger/south_migrations/0032_index_uuid.py

    operations = [
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS odk_logger_xform_uuid_idx ON logger_xform (uuid)"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS odk_logger_instance_uuid_idx ON logger_instance (uuid)"
        ),
    ]
