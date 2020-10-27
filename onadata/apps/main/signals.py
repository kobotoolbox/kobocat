# coding: utf-8
from __future__ import unicode_literals, print_function, division, absolute_import


def set_api_permissions(sender, instance=None, created=False, **kwargs):
    from onadata.libs.utils.user_auth import set_api_permissions_for_user
    if created:
        set_api_permissions_for_user(instance)
