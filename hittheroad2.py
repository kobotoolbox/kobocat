import csv
import datetime
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
# all_users_qs = User.objects.filter(username__in=('tino', 'tinok', 'tinok3', 'jamesld_test'))

usernames = [x.strip() for x in open('../kf-usernames.txt').readlines()]
all_users_qs = User.objects.filter(username__in=usernames)
csv_file_writer = csv.writer(open('/home/ubuntu/jnm-work/log/kf-kc.log', 'w'))


CHUNK_SIZE = 2000

counts = defaultdict(lambda: 1)

csv_writer = csv.writer(sys.stdout)


def print_csv(*args):
    csv_writer.writerow(args)
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

source_to_dest_pks = {}
source_to_dest_pks[User] = {-1: -1}  # PK for AnonymousUser doesn't change

# Even for Instances that belong to XForms owned by only a single user, it's
# necessary to cross-reference all users, since the user who submitted the
# instance could be anyone
source_user_xref = dict(all_users_qs.values_list('username', 'pk'))
with route_to_dest():
    for dest_user in all_users_qs.only('username'):
        source_to_dest_pks[User][
            source_user_xref[dest_user.username]
        ] = dest_user.pk


def copy_instances_for_single_username(single_username):
    xform_qs = XForm.objects.filter(user__username=single_username)

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
