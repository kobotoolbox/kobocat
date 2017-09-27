# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('logger', '0003_auto_20170810_0837'),
    ]

    operations = [
        migrations.AddField(
            model_name='backupinstance',
            name='uuid',
            field=models.CharField(default='', max_length=249),
        ),
        migrations.AddField(
            model_name='backupxform',
            name='migration_changes',
            field=models.TextField(default=''),
        ),
        migrations.AddField(
            model_name='backupxform',
            name='xform_id',
            field=models.PositiveIntegerField(default=1),
            preserve_default=False,
        ),
        migrations.AlterUniqueTogether(
            name='backupxform',
            unique_together=set([('xform_id', 'backup_version')]),
        ),
        migrations.RemoveField(
            model_name='backupxform',
            name='json',
        ),
    ]
