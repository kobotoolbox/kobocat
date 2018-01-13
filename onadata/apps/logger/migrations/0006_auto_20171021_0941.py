# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('logger', '0005_backupxform_id_string'),
    ]

    operations = [
        migrations.CreateModel(
            name='VersionTree',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('parent', models.ForeignKey(related_name='nodes', blank=True, to='logger.VersionTree', null=True)),
                ('version', models.OneToOneField(related_name='version_tree', null=True, blank=True, to='logger.BackupXForm')),
            ],
        ),
        migrations.AddField(
            model_name='xform',
            name='version_tree',
            field=models.ForeignKey(blank=True, to='logger.VersionTree', null=True),
        ),
    ]
