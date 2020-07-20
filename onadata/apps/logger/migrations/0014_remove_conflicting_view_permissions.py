# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('logger', '0013_remove_bamboo_and_ziggy_instance'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='xform',
            options={'ordering': ('id_string',), 'verbose_name': 'XForm', 'verbose_name_plural': 'XForms', 'permissions': (('report_xform', 'Can make submissions to the form'), ('transfer_xform', 'Can transfer form ownership.'), ('validate_xform', 'Can validate submissions.'))},
        ),
        migrations.AlterModelOptions(
            name='note',
            options={'permissions': ()},
        ),
    ]
