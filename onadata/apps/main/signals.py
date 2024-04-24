from django.db.models.signals import post_save
from django.dispatch import receiver
from guardian.shortcuts import assign_perm, get_perms_for_model
from rest_framework.authtoken.models import Token

from django.contrib.auth.models import User
from onadata.apps.main.models.user_profile import UserProfile
from onadata.libs.utils.user_auth import set_api_permissions_for_user


@receiver(post_save, sender=User, dispatch_uid='set_api_permissions')
def set_api_permissions(sender, instance=None, created=False, **kwargs):
    if created:
        set_api_permissions_for_user(instance)


@receiver(post_save, sender=User)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)


@receiver(post_save, sender=UserProfile, dispatch_uid='set_object_permissions')
def set_object_permissions(sender, instance=None, created=False, **kwargs):
    if created:
        for perm in get_perms_for_model(UserProfile):
            assign_perm(perm.codename, instance.user, instance)
