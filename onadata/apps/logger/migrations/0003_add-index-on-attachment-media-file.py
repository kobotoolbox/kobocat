# coding: utf-8
from __future__ import unicode_literals, print_function, division, absolute_import

from django.db import migrations, models
import onadata.apps.logger.models.attachment


class Migration(migrations.Migration):

    dependencies = [
        ('logger', '0002_attachment_filename_length'),
    ]

    operations = [
        migrations.AlterField(
            model_name='attachment',
            name='media_file',
            field=models.FileField(max_length=380, upload_to=onadata.apps.logger.models.attachment.upload_to, db_index=True),
        ),
    ]
