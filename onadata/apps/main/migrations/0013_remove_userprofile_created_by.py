# Generated by Django 3.2.15 on 2023-10-30 16:38

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0012_add_validate_password_flag_to_profile'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userprofile',
            name='created_by',
        ),
    ]
