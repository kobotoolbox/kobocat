# coding: utf-8
from __future__ import unicode_literals, print_function, division, absolute_import
from collections import defaultdict

from django.contrib.contenttypes.models import ContentType
from guardian.shortcuts import (
    assign_perm,
    remove_perm,
    get_perms,
    get_users_with_perms)

from onadata.apps.main.models.user_profile import UserProfile
from onadata.apps.logger.models import XForm

# Userprofile Permissions
CAN_ADD_USERPROFILE = 'add_userprofile'
CAN_CHANGE_USERPROFILE = 'change_userprofile'
CAN_DELETE_USERPROFILE = 'delete_userprofile'
CAN_ADD_XFORM_TO_PROFILE = 'can_add_xform'
CAN_VIEW_PROFILE = 'view_profile'

# Xform Permissions
CAN_CHANGE_XFORM = 'change_xform'
CAN_VALIDATE_XFORM = 'validate_xform'
CAN_ADD_XFORM = 'add_xform'
CAN_DELETE_XFORM = 'delete_xform'
CAN_VIEW_XFORM = 'view_xform'
CAN_ADD_SUBMISSIONS = 'report_xform'
CAN_TRANSFER_OWNERSHIP = 'transfer_xform'
CAN_MOVE_TO_FOLDER = 'move_xform'

CAN_ADD_DATADICTIONARY = 'add_datadictionary'
CAN_CHANGE_DATADICTIONARY = 'change_datadictionary'
CAN_DELETE_DATADICTIONARY = 'delete_datadictionary'


def get_object_users_with_permissions(obj, exclude=None, serializable=False):
    """Returns users, roles and permissions for a object.
    When called with with `serializable=True`, return usernames (strings)
    instead of User objects, which cannot be serialized by REST Framework.
    """
    result = []

    if obj:
        users_with_perms = get_users_with_perms(
            obj, attach_perms=True, with_group_users=False).items()

        result = [{
            'user': user if not serializable else user.username,
            'permissions': permissions} for user, permissions in
            users_with_perms
        ]

    return result
