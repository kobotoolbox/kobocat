# Generated by Django 2.2.28 on 2022-08-02 18:57

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('logger', '0024_add_xform_counters'),
    ]

    operations = [
        migrations.DeleteModel(
            name='SubmissionCounter',
        ),
    ]
