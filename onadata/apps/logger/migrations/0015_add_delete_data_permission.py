# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations
from django.contrib.auth.management import create_permissions
from django.contrib.auth.models import (
    Permission,
    User,
    AnonymousUser,
)


def forwards_func(apps, schema_editor):
    """
    All users need to receive the new permission at the model level.
    """
    # Permission does not exist when running this migration for the first time.
    # Django is running migrations in a transaction and permissions are created
    # after the transaction is completed.

    # ToDo update this code when upgrading to Django 2.x
    # see https://stackoverflow.com/a/40092780/1141214
    apps.models_module = True
    create_permissions(apps, verbosity=0)
    apps.models_module = None

    permission = Permission.objects.get(codename='delete_data_xform')
    users = User.objects.exclude(pk=AnonymousUser().pk)
    for user_ in users.all():
        user_.user_permissions.add(permission)


def reverse_func(apps, schema_editor):
    users = User.objects.exclude(pk=AnonymousUser().pk)
    permission = Permission.objects.get(codename='delete_data_xform')
    for user_ in users.all():
        user_.user_permissions.remove(permission)


class Migration(migrations.Migration):

    dependencies = [
        ('logger', '0014_attachment_add_media_file_size'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='xform',
            options={'ordering': ('id_string',), 'verbose_name': 'XForm', 'verbose_name_plural': 'XForms', 'permissions': (('view_xform', 'Can view associated data'), ('report_xform', 'Can make submissions to the form'), ('move_xform', 'Can move form between projects'), ('transfer_xform', 'Can transfer form ownership'), ('validate_xform', 'Can validate submissions'), ('delete_data_xform', 'Can delete submissions'))},
        ),
        # This can take a while on big databases
        migrations.RunPython(forwards_func, reverse_func),
    ]
