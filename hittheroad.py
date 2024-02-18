import csv
import sys
from collections import defaultdict
from copy import deepcopy
from itertools import islice

from django.db.models import Prefetch
from django.contrib.contenttypes.models import ContentType

from onadata.libs.utils.user_auth import set_api_permissions_for_user
from onadata.settings.hittheroad import HitTheRoadDatabaseRouter
route_to_dest = HitTheRoadDatabaseRouter.route_to_destination

# Imports are in a weird order because below are the models being copied

from django.contrib.auth.models import User, Permission
from onadata.apps.main.models.user_profile import UserProfile
# from django.contrib.auth.models import User_user_permissions
from django_digest.models import PartialDigest
from rest_framework.authtoken.models import Token
from onadata.apps.logger.models.xform import XForm

from onadata.apps.restservice.models import RestService
from onadata.apps.main.models.meta_data import MetaData
from guardian.models.models import UserObjectPermission

from onadata.apps.logger.models.instance import Instance
from onadata.apps.viewer.models.parsed_instance import ParsedInstance
from onadata.apps.logger.models.attachment import Attachment
from onadata.apps.logger.models.note import Note
# handled by calling _set_survey_type() during Instance migration
# from onadata.apps.logger.models.survey_type import SurveyType


# to be replaced by reading usernames from a file
all_users_qs = User.objects.filter(username__startswith='moveme')




CHUNK_SIZE = 2000

counts = defaultdict(lambda: 1)

csv_writer = csv.writer(sys.stdout)


def print_csv(*args):
    csv_writer.writerow(args)


def legible_class(cls):
    return f'{cls.__module__}.{cls.__name__}'


class SkipObject(Exception):
    pass


def disable_auto_now(model):
    for field in model._meta.fields:
        for bad in ('auto_now', 'auto_now_add'):
            if hasattr(field, bad):
                setattr(field, bad, False)


def copy_related_objs(
    qs,
    related_fk_field,
    related_qs,
    nat_key: list = None,
    retain_pk=False,
    fixup: callable = None,
):
    disable_auto_now(qs.model)
    obj_iter = qs.filter(**{related_fk_field + '__in': related_qs}).iterator(
        chunk_size=CHUNK_SIZE
    )
    related_id_field = f'{related_fk_field}_id'
    try:
        related_source_to_dest_pks = source_to_dest_pks[related_qs.model]
    except KeyError:
        raise Exception(
            f'{related_qs.model} must be copied with `nat_key` specified before'
            f' {qs.model} can be copied'
        )
    this_model_source_to_dest_pks = source_to_dest_pks.setdefault(qs.model, {})
    while True:
        objs = list(islice(obj_iter, CHUNK_SIZE))
        if not objs:
            break
        nat_key_to_source_pks = {}
        objs_to_create = []
        for obj in objs:
            print_csv(
                legible_class(qs.model), obj.pk, f'({counts[qs.model]} done)'
            )
            counts[qs.model] += 1
            source_obj_pk = obj.pk
            if nat_key:
                nat_key_vals = tuple(getattr(obj, f) for f in nat_key)
                nat_key_to_source_pks[nat_key_vals] = source_obj_pk
            if not retain_pk:
                obj.pk = None
            source_related_id = getattr(obj, related_id_field)
            try:
                dest_related_id = related_source_to_dest_pks[source_related_id]
            except KeyError:
                raise Exception(
                    f'{qs.model} # {source_obj_pk} expects {related_qs.model}'
                    f' # {source_related_id}, but it has not been copied'
                )
            setattr(obj, related_id_field, dest_related_id)
            if fixup:
                # We don't have all the time in the world… apply any necessary
                # hacks here
                try:
                    fixup(obj)
                except SkipObject:
                    continue
            objs_to_create.append(obj)
        with route_to_dest():
            created_objs = qs.model.objects.bulk_create(objs_to_create)
        if nat_key:
            for created_obj in created_objs:
                nat_key_vals = tuple(getattr(created_obj, f) for f in nat_key)
                this_model_source_to_dest_pks[
                    nat_key_to_source_pks[nat_key_vals]
                ] = created_obj.pk


source_to_dest_pks = {}
source_to_dest_pks[User] = {-1: -1}  # PK for AnonymousUser doesn't change

for user in all_users_qs.only('username'):
    print_csv(
        legible_class(User), user.pk, user.username, f'({counts[User]} done)'
    )
    counts[User] += 1
    source_user_pk = user.pk
    with route_to_dest():
        # Rely on the user having already been created by the KPI migration
        user = User.objects.get(username=user.username)
        # like kpi's grant_default_model_level_perms()
        set_api_permissions_for_user(user)

    source_to_dest_pks[User][source_user_pk] = user.pk

    user_qs = User.objects.filter(username=user.username)

    # Directly related to User

    copy_related_objs(UserProfile.objects.all(), 'user', user_qs)
    copy_related_objs(PartialDigest.objects.all(), 'user', user_qs)
    copy_related_objs(Token.objects.all(), 'user', user_qs, retain_pk=True)
    copy_related_objs(
        XForm.objects.all(), 'user', user_qs, ['id_string', 'uuid']
    )

    # Related to XForm

    xform_qs = XForm.objects.filter(user__in=user_qs)

    copy_related_objs(
        RestService.objects.all(),
        'xform',
        xform_qs,
        # ['xform', 'service_url', 'name'],
    )

    copy_related_objs(
        MetaData.objects.all(),
        'xform',
        xform_qs,
        # ['data_type', 'data_value'],
    )


def call_set_survey_type(instance):
    with route_to_dest():
        instance._set_survey_type()


def update_user_pk(obj):
    try:
        obj.user_id = source_to_dest_pks[User][obj.user_id]
    except KeyError:
        # If the submitting user is not also being migrated, null out the
        # field
        obj.user_id = None


def update_user_pk_and_call_set_survey_type(instance):
    update_user_pk(instance)
    call_set_survey_type(instance)


def call_update_mongo(parsedinstance):
    with route_to_dest():
        parsedinstance.update_mongo(asynchronous=False)


# Things that depend on all users having been copied already

for user in all_users_qs.only('username'):
    # Loop through users again to handle Instances, which could've been
    # submitted by any user
    xform_qs = XForm.objects.filter(user__username=user.username)

    copy_related_objs(
        Instance.objects.all(),
        'xform',
        xform_qs,
        ['uuid', 'xml_hash', 'date_created', 'date_modified'],
        fixup=update_user_pk_and_call_set_survey_type,
    )

    # Related to Instance

    instance_qs = Instance.objects.filter(xform__in=xform_qs)

    copy_related_objs(
        ParsedInstance.objects.all(),
        'instance',
        instance_qs,
        fixup=call_update_mongo,
    )

    copy_related_objs(
        Attachment.objects.all(),
        'instance',
        instance_qs,
    )

    copy_related_objs(
        Note.objects.all(),
        'instance',
        instance_qs,
    )

# Cross-reference Permissions by app_label and model (from ContentType) and
# codename

source_permissions = list(
    Permission.objects.all().select_related('content_type')
)
source_permissions_xref = {
    (p.content_type.app_label, p.content_type.model, p.codename): p.pk
    for p in source_permissions
}
with route_to_dest():
    dest_permissions = list(
        Permission.objects.all().select_related('content_type')
    )
source_to_dest_pks[Permission] = {}
for p in dest_permissions:
    source_to_dest_pks[Permission][
        source_permissions_xref[
            (p.content_type.app_label, p.content_type.model, p.codename)
        ]
    ] = p.pk


def update_permission_pk(obj_related_to_permission):
    obj_related_to_permission.permission_id = source_to_dest_pks[Permission][
        obj_related_to_permission.permission_id
    ]


source_xform_ct = ContentType.objects.get_for_model(XForm)
with route_to_dest():
    dest_xform_ct = ContentType.objects.get_for_model(XForm)
source_to_dest_pks[ContentType] = {source_xform_ct.pk: dest_xform_ct.pk}


def update_xform_generic_fk(obj):
    try:
        obj.object_pk = source_to_dest_pks[XForm][int(obj.object_pk)]
    except KeyError:
        # Ignore permission assignments for XForms that are not part of the
        # migration
        raise SkipObject
    obj.content_type_id = source_to_dest_pks[ContentType][obj.content_type_id]


def fixup_guardian_perm(obj):
    update_xform_generic_fk(obj)
    update_permission_pk(obj)


copy_related_objs(
    UserObjectPermission.objects.filter(content_type=source_xform_ct),
    'user',
    all_users_qs,
    fixup=fixup_guardian_perm,
)


''' Zafacón
def DEBUG__clean_up():
    with route_to_dest():
        # `QuerySet.all()` copies the queryset. Is it necessary…?
        print(all_users_qs.all().delete())
'''
