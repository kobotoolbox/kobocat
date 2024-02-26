import csv
import datetime
import sys
from collections import defaultdict


from onadata.settings.hittheroad import HitTheRoadDatabaseRouter
route_to_dest = HitTheRoadDatabaseRouter.route_to_destination


# Imports are in a weird order because below are the models being copied

from django.contrib.auth.models import User

from onadata.apps.logger.models.xform import XForm

from onadata.apps.restservice.models import RestService
from onadata.apps.main.models.meta_data import MetaData

from onadata.apps.logger.models.instance import Instance
from onadata.apps.viewer.models.parsed_instance import ParsedInstance
from onadata.apps.logger.models.attachment import Attachment
from onadata.apps.logger.models.note import Note
from onadata.apps.logger.models.survey_type import SurveyType


usernames = set(
    x.strip() for x in open('xform-oriented-copy-usernames.txt').readlines()
)
csv_file_writer = csv.writer(
    open(f'xform-oriented-copy-{datetime.datetime.now()}.log', 'w')
)
counts = defaultdict(lambda: 1)
csv_writer = csv.writer(sys.stdout)
source_to_dest_pks = {}
source_to_dest_pks[User] = {-1: -1}  # PK for AnonymousUser doesn't change


class SkipObject(Exception):
    pass


def print_csv(*args):
    csv_writer.writerow((datetime.datetime.now(),) + args)
    csv_file_writer.writerow((datetime.datetime.now(),) + args)


def legible_class(cls):
    return f'{cls.__module__}.{cls.__name__}'


def xref_source_and_dest_users():
    all_users_qs = User.objects.filter(username__in=usernames)
    source_user_xref = dict(all_users_qs.values_list('username', 'pk'))
    not_found_source_usernames = usernames.difference(source_user_xref.keys())
    if not_found_source_usernames:
        raise Exception(
            '🛑 Users were not found in the source database: ',
            +','.join(not_found_source_usernames),
        )
    with route_to_dest():
        for dest_user in all_users_qs.only('username'):
            source_to_dest_pks[User][
                source_user_xref[dest_user.username]
            ] = dest_user.pk
    not_found_dest_usernames = usernames.difference(
        source_to_dest_pks[User].keys()
    )
    if not_found_dest_usernames:
        raise Exception(
            '🛑 Users were not found in the destination database: ',
            +','.join(not_found_dest_usernames),
        )


def disable_auto_now(model):
    for field in model._meta.fields:
        for bad in ('auto_now', 'auto_now_add'):
            if hasattr(field, bad):
                setattr(field, bad, False)


def copy_related_obj(
    obj,
    related_fk_field,
    nat_key: list = None,
    retain_pk=False,
    fixup: callable = None,
):
    model = type(obj)
    disable_auto_now(model)  # never reenable within this single-use process
    related_field = model._meta.get_field(related_fk_field)
    related_id_attr = related_field.attname
    related_model = related_field.related_model
    try:
        related_source_to_dest_pks = source_to_dest_pks[related_model]
    except KeyError:
        raise Exception(
            f'{related_model} must be copied with `nat_key` specified before'
            f' {model} can be copied'
        )
    this_model_source_to_dest_pks = source_to_dest_pks.setdefault(model, {})
    source_obj_pk = obj.pk
    if not retain_pk:
        obj.pk = None
    source_related_id = getattr(obj, related_id_attr)
    try:
        dest_related_id = related_source_to_dest_pks[source_related_id]
    except KeyError:
        raise Exception(
            f'{legible_class(model)} #{source_obj_pk} expects {related_model}'
            f' #{source_related_id}, but it has not been copied'
        )
    setattr(obj, related_id_attr, dest_related_id)
    if fixup:
        # We don't have all the time in the world… apply any necessary
        # hacks here
        try:
            fixup(obj)
        except SkipObject:
            return obj
    if not nat_key:
        model.objects.bulk_create([obj])
    else:
        nat_key_vals = tuple(getattr(obj, f) for f in nat_key)
        with route_to_dest():
            try:
                criteria = dict(zip(nat_key, nat_key_vals))
                criteria[related_id_attr] = dest_related_id
                obj = model.objects.get(**criteria)
            except model.DoesNotExist:
                # "bulk create" single item to sidestep `save()` logic
                model.objects.bulk_create([obj])
            else:
                print_csv(
                    f'ℹ️ {legible_class(model)}',
                    source_obj_pk,
                    obj.pk,
                    '(already exists!)',
                )
        this_model_source_to_dest_pks[source_obj_pk] = obj.pk
    print_csv(
        f'✅ {legible_class(model)}',
        source_obj_pk,
        obj.pk,
        f'({counts[model]} done)',
    )
    counts[model] += 1
    return obj


def set_survey_type(instance, survey_type_slug_to_dest_pk_cache={}):
    # just calling Instance._set_survey_type() was leaking tons of memory (and
    # slow)
    with route_to_dest():
        instance.survey_type_id = survey_type_slug_to_dest_pk_cache.setdefault(
            instance.survey_type_id,
            SurveyType.objects.get_or_create(slug=instance.survey_type.slug)[
                0
            ].pk,
        )


def update_user_pk(obj):
    try:
        obj.user_id = source_to_dest_pks[User][obj.user_id]
    except KeyError:
        # If the submitting user is not also being migrated, null out the
        # field
        obj.user_id = None


def update_user_pk_and_set_survey_type(instance):
    update_user_pk(instance)
    set_survey_type(instance)


def copy_xforms():
    xref_source_and_dest_users()
    print(f'✅ Cross-referenced {len(source_to_dest_pks[User])} users')
    xform_qs = XForm.objects.filter(user__username__in=usernames)
    for xform in xform_qs.iterator():
        xform_source_pk = xform.pk
        copy_related_obj(xform, 'user', ['id_string', 'uuid'])

        # Easy stuff (likely not many of these)
        rest_service_qs = RestService.objects.filter(xform_id=xform_source_pk)
        meta_data_qs = MetaData.objects.filter(xform_id=xform_source_pk)
        for rest_service in rest_service_qs.iterator():
            copy_related_obj(rest_service, 'xform', ['service_url', 'name'])
        for meta_data in meta_data_qs.iterator():
            copy_related_obj(meta_data, 'xform', ['data_type', 'data_value'])

        # Hard stuff! Could be millions
        instance_qs = Instance.objects.filter(xform_id=xform_source_pk)
        for instance in instance_qs.iterator():
            instance_source_pk = instance.pk
            copy_related_obj(
                instance,
                'xform',
                ['uuid', 'xml_hash', 'date_created', 'date_modified'],
                fixup=update_user_pk_and_set_survey_type,
            )
            with route_to_dest():
                try:
                    parsed_instance = ParsedInstance.objects.get(
                        instance_id=instance.pk
                    )
                except ParsedInstance.DoesNotExist:
                    parsed_instance = None
            if not parsed_instance:
                # Set `metadata['submissions_suspended'] = True` on
                # `UserProfile`s in the destination database to avoid race
                # conditions
                copy_related_obj(
                    ParsedInstance.objects.get(instance_id=instance_source_pk),
                    'instance',
                )
            for mod_related_to_instance in (Attachment, Note):
                mod_qs = mod_related_to_instance.objects.filter(
                    instance_id=instance_source_pk
                )
                for obj in mod_qs.iterator():
                    copy_related_obj(obj, 'instance')
