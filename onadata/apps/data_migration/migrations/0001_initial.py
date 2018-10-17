# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import onadata.apps.logger.models.xform
import django.core.files.storage
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('logger', '0007_add_validate_permission_on_xform'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='BackupInstance',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('xml', models.TextField()),
                ('date_created', models.DateTimeField()),
                ('uuid', models.CharField(default='', max_length=249)),
                ('user', models.ForeignKey(related_name='backup_surveys', to=settings.AUTH_USER_MODEL, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='BackupXForm',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('xform_id', models.PositiveIntegerField()),
                ('xls', models.FileField(storage=django.core.files.storage.FileSystemStorage(), null=True, upload_to=onadata.apps.logger.models.xform.upload_to)),
                ('xml', models.TextField()),
                ('description', models.TextField(default='', null=True)),
                ('id_string', models.CharField(max_length=100)),
                ('_migration_changes', models.TextField(default='')),
                ('date_created', models.DateTimeField()),
                ('backup_version', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(related_name='backup_xforms', to=settings.AUTH_USER_MODEL, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='VersionTree',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('parent', models.ForeignKey(related_name='nodes', blank=True, to='data_migration.VersionTree', null=True)),
                ('version', models.OneToOneField(related_name='version_tree', null=True, blank=True, to='data_migration.BackupXForm')),
            ],
        ),
        migrations.CreateModel(
            name='XFormVersion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('version_tree', models.ForeignKey(blank=True, to='data_migration.VersionTree', null=True)),
                ('xform', models.OneToOneField(to='logger.XForm')),
            ],
        ),
        migrations.AddField(
            model_name='backupinstance',
            name='xform',
            field=models.ForeignKey(related_name='surveys', to='data_migration.BackupXForm', null=True),
        ),
        migrations.AlterUniqueTogether(
            name='backupxform',
            unique_together=set([('xform_id', 'backup_version')]),
        ),
    ]
