# coding: utf-8
from __future__ import unicode_literals, print_function, division, absolute_import
from django.core.management.base import BaseCommand
from django.utils.translation import gettext as _

from onadata.apps.api.models.organization_profile import OrganizationProfile
from onadata.apps.logger.models.xform import XForm
from onadata.apps.main.models.user_profile import UserProfile
from onadata.libs.utils.model_tools import queryset_iterator
from onadata.libs.utils.user_auth import set_api_permissions_for_user


class Command(BaseCommand):
    help = _("Set object permissions for all objects.")

    # TODO: unprojectify
    '''
    def handle(self, *args, **options):
        # XForms
        for xform in queryset_iterator(XForm.objects.all()):
            OwnerRole.add(xform.user, xform)

        # UserProfile
        for profile in queryset_iterator(UserProfile.objects.all()):
            set_api_permissions_for_user(profile.user)
            OwnerRole.add(profile.user, profile)

            if profile.created_by is not None:
                OwnerRole.add(profile.created_by, profile)
    '''
