# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import onadata.apps.logger.models.xform
import django.core.files.storage
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('logger', '0002_attachment_filename_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='BackupInstance',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('xml', models.TextField()),
                ('date_created', models.DateTimeField()),
                ('user', models.ForeignKey(related_name='backup_surveys', to=settings.AUTH_USER_MODEL, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='BackupXForm',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('xls', models.FileField(storage=django.core.files.storage.FileSystemStorage(), null=True, upload_to=onadata.apps.logger.models.xform.upload_to)),
                ('xml', models.TextField()),
                ('json', models.TextField(default='')),
                ('description', models.TextField(default='', null=True)),
                ('date_created', models.DateTimeField()),
                ('backup_version', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(related_name='backup_xforms', to=settings.AUTH_USER_MODEL, null=True)),
            ],
        ),
        migrations.AddField(
            model_name='backupinstance',
            name='xform',
            field=models.ForeignKey(related_name='surveys', to='logger.BackupXForm', null=True),
        ),
    ]
