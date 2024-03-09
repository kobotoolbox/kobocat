"""
What does this do?

It will copy `Instance`s and related objects for `XForm`s owned by the username
specified on the command line.

The code is commented out, but there's logic to create missing `XForm`s in the
destination database where needed. *HOWEVER*, this logic does nothing to handle
related objects like `RestService`s, `MetaData`s, or `UserObjectPermission`s
"""

import csv
import datetime
import sys
from itertools import islice
from collections import defaultdict

from django.contrib.auth.models import User

from onadata.apps.logger.models.attachment import Attachment
from onadata.apps.logger.models.instance import Instance
from onadata.apps.logger.models.note import Note
from onadata.apps.logger.models.survey_type import SurveyType
from onadata.apps.logger.models.xform import XForm
from onadata.apps.viewer.models.parsed_instance import ParsedInstance
from onadata.settings.hittheroad import HitTheRoadDatabaseRouter

route_to_dest = HitTheRoadDatabaseRouter.route_to_destination

CHUNK_SIZE = 1000
counts = defaultdict(lambda: 1)
csv_writer = csv.writer(sys.stdout)
csv_file_writer = csv.writer(
    open(f'copy-instances-and-related-{datetime.datetime.now()}.log', 'w')
)
source_to_dest_pks = {}


class SkipObject(Exception):
    pass


def xref_all_users():
    with route_to_dest():
        dest_usernames_to_pks = {
            v[0]: v[1] for v in User.objects.values_list('username', 'pk')
        }
    source_usernames_to_pks = {
        v[0]: v[1]
        for v in User.objects.filter(
            username__in=dest_usernames_to_pks.keys()
        ).values_list('username', 'pk')
    }
    source_to_dest_pks[User] = {}
    for username, dest_pk in dest_usernames_to_pks.items():
        try:
            source_pk = source_usernames_to_pks[username]
        except KeyError:
            continue
        source_to_dest_pks[User][source_pk] = dest_pk


def xref_xforms(xform_qs):
    source_to_dest_pks[XForm] = {}
    source_xform_xref = {
        (id_string, uuid): pk
        for (id_string, uuid, pk) in xform_qs.values_list(
            'id_string', 'uuid', 'pk'
        )
    }
    with route_to_dest():
        for dest_xform in xform_qs.only('id_string', 'uuid'):
            source_to_dest_pks[XForm][
                source_xform_xref[(dest_xform.id_string, dest_xform.uuid)]
            ] = dest_xform.pk


def disable_auto_now(model):
    for field in model._meta.fields:
        for bad in ('auto_now', 'auto_now_add'):
            if hasattr(field, bad):
                setattr(field, bad, False)


def print_csv(*args):
    csv_writer.writerow((datetime.datetime.now(),) + args)
    csv_file_writer.writerow((datetime.datetime.now(),) + args)


def legible_class(cls):
    return f'{cls.__module__}.{cls.__name__}'


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


def copy_related_obj(
    obj,
    related_fk_field,
    nat_key: list = None,
    retain_pk=False,
    fixup: callable = None,
):
    # Yay, code duplication
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
    status = 'done'
    if not nat_key:
        with route_to_dest():
            model.objects.bulk_create([obj])
    else:
        nat_key_vals = tuple(getattr(obj, f) for f in nat_key)
        with route_to_dest():
            criteria = dict(zip(nat_key, nat_key_vals))
            criteria[related_id_attr] = dest_related_id
            try:
                existing_obj = model.objects.get(**criteria)
            except model.DoesNotExist:
                # "bulk create" single item to sidestep `save()` logic
                model.objects.bulk_create([obj])
            else:
                obj.pk = existing_obj.pk
                status ='already exists!'
        this_model_source_to_dest_pks[source_obj_pk] = obj.pk
    print_csv(
        f'✅ {legible_class(model)}',
        source_obj_pk,
        obj.pk,
        status,
        f'(complete: {counts[model]})',
    )
    counts[model] += 1
    return obj


def check_for_missing_parsedinstances(username):
    """
    This is for fixing up an interrupted migration. It is
    NOT CALLED unless you call it manually!
    """

    print(f'Username {username}')

    instance_nat_key_fields = [
        'uuid',
        'xml_hash',
        'date_created',
        'date_modified',
    ]

    source_instance_nat_key_to_pks = {}
    count = 0
    for vals in (
        Instance.objects.filter(xform__user__username=username)
        .values_list(*(['pk'] + instance_nat_key_fields))
        .iterator()
    ):
        source_instance_nat_key_to_pks[tuple(vals[1:])] = vals[0]
        count += 1
        print(f'\r{count} source instances', end='', flush=True)
    print()

    source_to_dest_pks[Instance] = {}
    dest_instance_nat_key_to_pks = {}
    count = 0
    with route_to_dest():
        for vals in (
            Instance.objects.filter(xform__user__username=username)
            .values_list(*(['pk'] + instance_nat_key_fields))
            .iterator()
        ):
            nat_key_vals = tuple(vals[1:])
            dest_instance_nat_key_to_pks[nat_key_vals] = vals[0]
            count += 1
            print(f'\r{count} dest instances', end='', flush=True)
            try:
                source_pk = source_instance_nat_key_to_pks[nat_key_vals]
            except KeyError:
                pass  # It was deleted from the source? Oh well
            else:
                source_to_dest_pks[Instance][source_pk] = vals[0]
        print()

    source_to_dest_pks[Instance]

    parsedinstance_nat_key_fields = [
        'instance__uuid',
        'instance__xml_hash',
        'instance__date_created',
        'instance__date_modified',
    ]

    source_parsedinstance_nat_key_to_pks = {}
    count = 0
    count_parsedinstances_for_post_migration_instances = 0
    for vals in (
        ParsedInstance.objects.filter(instance__xform__user__username=username)
        .values_list(*(['pk'] + parsedinstance_nat_key_fields))
        .iterator()
    ):
        count += 1
        print(f'\r{count} source parsedinstances', end='', flush=True)

        instance_nat_key_vals = tuple(
            vals[i + 1]
            for i, field in enumerate(parsedinstance_nat_key_fields)
            if field.startswith('instance__')
        )
        if instance_nat_key_vals in dest_instance_nat_key_to_pks:
            # At this phase, instance copying has completed. Only consider
            # parsedinstances for instances already on the destination
            source_parsedinstance_nat_key_to_pks[tuple(vals[1:])] = vals[0]
        else:
            count_parsedinstances_for_post_migration_instances += 1
    print()

    dest_parsedinstance_nat_key_to_pks = {}
    count = 0
    with route_to_dest():
        for vals in (
            ParsedInstance.objects.filter(
                instance__xform__user__username=username
            )
            .values_list(*(['pk'] + parsedinstance_nat_key_fields))
            .iterator()
        ):
            dest_parsedinstance_nat_key_to_pks[tuple(vals[1:])] = vals[0]
            count += 1
            print(f'\r{count} dest parsedinstances', end='', flush=True)
        print()

    print(
        f'{count_parsedinstances_for_post_migration_instances} parsedinstances'
        ' were ignored because they belong to post-migration instances'
    )

    parsedinstance_nat_keys_in_source_only = set(
        source_parsedinstance_nat_key_to_pks.keys()
    ).difference(dest_parsedinstance_nat_key_to_pks.keys())
    print(
        f'{len(parsedinstance_nat_keys_in_source_only)} parsedinstances need to'
        ' be copied'
    )
    if not parsedinstance_nat_keys_in_source_only:
        return

    parsedinstance_qs = ParsedInstance.objects.filter(
        pk__in=[
            source_parsedinstance_nat_key_to_pks[vals]
            for vals in parsedinstance_nat_keys_in_source_only
        ]
    )
    copy_related_objs(
        parsedinstance_qs,
        'instance',
        # Would be better to refactor the function to accept a model instead of
        # a queryset when no filtering by related objects is needed. Hopefully
        # the database is smart enough to optimize it away
        Instance.objects.all(),
    )


def check_for_missing_attachments(username):
    """
    This is for fixing up an interrupted migration. It is
    NOT CALLED unless you call it manually!
    """

    print(f'Username {username}')

    instance_nat_key_fields = [
        'uuid',
        'xml_hash',
        'date_created',
        'date_modified',
    ]

    source_instance_nat_key_to_pks = {}
    count = 0
    for vals in (
        Instance.objects.filter(xform__user__username=username)
        .values_list(*(['pk'] + instance_nat_key_fields))
        .iterator()
    ):
        source_instance_nat_key_to_pks[tuple(vals[1:])] = vals[0]
        count += 1
        print(f'\r{count} source instances', end='', flush=True)
    print()

    source_to_dest_pks[Instance] = {}
    dest_instance_nat_key_to_pks = {}
    count = 0
    with route_to_dest():
        for vals in (
            Instance.objects.filter(xform__user__username=username)
            .values_list(*(['pk'] + instance_nat_key_fields))
            .iterator()
        ):
            nat_key_vals = tuple(vals[1:])
            dest_instance_nat_key_to_pks[nat_key_vals] = vals[0]
            count += 1
            print(f'\r{count} dest instances', end='', flush=True)
            try:
                source_pk = source_instance_nat_key_to_pks[nat_key_vals]
            except KeyError:
                pass  # It was deleted from the source? Oh well
            else:
                source_to_dest_pks[Instance][source_pk] = vals[0]
        print()

    source_to_dest_pks[Instance]

    attachment_nat_key_fields = [
        'instance__uuid',
        'instance__xml_hash',
        'instance__date_created',
        'instance__date_modified',
        'media_file',
        'media_file_size',
    ]

    source_attachment_nat_key_to_pks = {}
    count = 0
    count_attachments_for_post_migration_instances = 0
    for vals in (
        Attachment.objects.filter(instance__xform__user__username=username)
        .values_list(*(['pk'] + attachment_nat_key_fields))
        .iterator()
    ):
        count += 1
        print(f'\r{count} source attachments', end='', flush=True)

        instance_nat_key_vals = tuple(
            vals[i + 1]
            for i, field in enumerate(attachment_nat_key_fields)
            if field.startswith('instance__')
        )
        if instance_nat_key_vals in dest_instance_nat_key_to_pks:
            # At this phase, instance copying has completed. Only consider
            # attachments for instances already on the destination
            source_attachment_nat_key_to_pks[tuple(vals[1:])] = vals[0]
        else:
            count_attachments_for_post_migration_instances += 1
    print()

    dest_attachment_nat_key_to_pks = {}
    count = 0
    with route_to_dest():
        for vals in (
            Attachment.objects.filter(instance__xform__user__username=username)
            .values_list(*(['pk'] + attachment_nat_key_fields))
            .iterator()
        ):
            dest_attachment_nat_key_to_pks[tuple(vals[1:])] = vals[0]
            count += 1
            print(f'\r{count} dest attachments', end='', flush=True)
        print()

    print(
        f'{count_attachments_for_post_migration_instances} attachments were'
        ' ignored because they belong to post-migration instances'
    )

    attachment_nat_keys_in_source_only = set(
        source_attachment_nat_key_to_pks.keys()
    ).difference(dest_attachment_nat_key_to_pks.keys())
    print(
        f'{len(attachment_nat_keys_in_source_only)} attachments need to be'
        ' copied'
    )
    if not attachment_nat_keys_in_source_only:
        return

    attachment_qs = Attachment.objects.filter(
        pk__in=[
            source_attachment_nat_key_to_pks[vals]
            for vals in attachment_nat_keys_in_source_only
        ]
    )
    copy_related_objs(
        attachment_qs,
        'instance',
        # Would be better to refactor the function to accept a model instead of
        # a queryset when no filtering by related objects is needed. Hopefully
        # the database is smart enough to optimize it away
        Instance.objects.all()
    )


def run(username):
    print(f'Username {username}')

    instance_nat_key_fields = [
        'uuid',
        'xml_hash',
        'date_created',
        'date_modified',
    ]

    source_instance_nat_key_to_pks = {}
    count = 0
    for vals in (
        Instance.objects.filter(xform__user__username=username)
        .values_list(*(['pk'] + instance_nat_key_fields))
        .iterator()
    ):
        source_instance_nat_key_to_pks[tuple(vals[1:])] = vals[0]
        count += 1
        print(f'\r{count} source instances', end='', flush=True)
    print()

    dest_instance_nat_key_to_pks = {}
    count = 0
    with route_to_dest():
        for vals in (
            Instance.objects.filter(xform__user__username=username)
            .values_list(*(['pk'] + instance_nat_key_fields))
            .iterator()
        ):
            dest_instance_nat_key_to_pks[tuple(vals[1:])] = vals[0]
            count += 1
            print(f'\r{count} dest instances', end='', flush=True)
        print()

    nat_keys_in_source_only = set(
        source_instance_nat_key_to_pks.keys()
    ).difference(dest_instance_nat_key_to_pks.keys())
    print(f'{len(nat_keys_in_source_only)} instances need to be copied')

    if not nat_keys_in_source_only:
        return

    print('Cross-referencing all users…', end='', flush=True)
    xref_all_users()
    print(' done!')

    xform_qs = XForm.objects.filter(user__username=username)
    print('Cross-referencing XForms…', end='', flush=True)
    xref_xforms(xform_qs)
    print(' done!')

    # If you need to create missing XForms on the fly, you can--but you'll have
    # to deal with their related objects somehow
    '''
    # By gosh, they're still creating XForms!
    for xform in xform_qs.iterator():
        copy_related_obj(xform, 'user', ['id_string', 'uuid'])
    '''

    instance_pks_in_source_only = [
        source_instance_nat_key_to_pks[nk] for nk in nat_keys_in_source_only
    ]
    instance_qs = Instance.objects.filter(pk__in=instance_pks_in_source_only)

    copy_related_objs(
        instance_qs.select_related('survey_type'),
        'xform',
        xform_qs,
        ['uuid', 'xml_hash', 'date_created', 'date_modified'],
        fixup=update_user_pk_and_set_survey_type,
    )

    copy_related_objs(
        ParsedInstance.objects.all(),
        'instance',
        instance_qs,
        # hits a memory leak in pyxform?
        # without it we have to run `./manage.py sync_mongo` afterwards :sad:
        # fixup=call_update_mongo,
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
