"""

This is a pretty limited mechanism to copy django-guardian
`UserObjectPermission`s after all `User`s and `XForm`s have already been
copied. It fails to handle permissions assigned to users beyond those listed in
`htr-usernames.txt`. It also does not copy anything else related to `XForm`, so
it does not suffice for overall clean-up after piecemeal copy of `XForm`s.

"""

import csv
import datetime
import sys
from collections import defaultdict
from itertools import islice

from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User, Permission
from guardian.models.models import UserObjectPermission

from onadata.apps.logger.models.xform import XForm
from onadata.settings.hittheroad import HitTheRoadDatabaseRouter
route_to_dest = HitTheRoadDatabaseRouter.route_to_destination


usernames = [x.strip() for x in open('htr-usernames.txt').readlines()]
all_users_qs = User.objects.filter(username__in=usernames)
csv_file_writer = csv.writer(
    open(f'kc-hittheroad3-{datetime.datetime.now()}.log', 'w')
)


CHUNK_SIZE = 1000

counts = defaultdict(lambda: 1)

csv_writer = csv.writer(sys.stdout)


def print_csv(*args):
    csv_writer.writerow((datetime.datetime.now(),) + args)
    csv_file_writer.writerow((datetime.datetime.now(),) + args)


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


# Things that depend on all users having been copied already

source_to_dest_pks = {}
source_to_dest_pks[User] = {-1: -1}  # PK for AnonymousUser doesn't change

# Set up cross references for all Users and XForms (these were already copied)

source_user_xref = dict(all_users_qs.values_list('username', 'pk'))
with route_to_dest():
    for dest_user in all_users_qs.only('username'):
        source_to_dest_pks[User][
            source_user_xref[dest_user.username]
        ] = dest_user.pk


xform_qs = XForm.objects.filter(user__username__in=usernames)
source_to_dest_pks[XForm] = {}
source_xform_xref = {
    (id_string, uuid): pk
    for (id_string, uuid, pk) in xform_qs.values_list('id_string', 'uuid', 'pk')
}
with route_to_dest():
    for dest_xform in xform_qs.only('id_string', 'uuid'):
        source_to_dest_pks[XForm][
            source_xform_xref[(dest_xform.id_string, dest_xform.uuid)]
        ] = dest_xform.pk


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
    try:
        source_pk = source_permissions_xref[
            (p.content_type.app_label, p.content_type.model, p.codename)
        ]
    except KeyError:
        continue
    source_to_dest_pks[Permission][source_pk] = p.pk


def update_permission_pk(obj_related_to_permission):
    try:
        obj_related_to_permission.permission_id = source_to_dest_pks[
            Permission
        ][obj_related_to_permission.permission_id]
    except KeyError:
        raise SkipObject


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
