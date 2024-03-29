# Generated by Django 3.2.15 on 2023-11-02 15:30
from itertools import islice
from urllib.parse import urlparse

from django.conf import settings
from django.db import migrations
from django_redis import get_redis_connection


CHUNK_SIZE = 2000


def restore_open_rosa_server_in_redis(apps, schema_editor):

    if settings.SKIP_HEAVY_MIGRATIONS:
        return

    print(
        """
        This migration might take a while. If it is too slow, you may want to
        re-run migrations with SKIP_HEAVY_MIGRATIONS=True and apply this one
        manually from the django shell.
        """
    )

    XForm = apps.get_model('logger', 'XForm')  # noqa

    parsed_url = urlparse(settings.KOBOCAT_URL)
    server_url = settings.KOBOCAT_URL.rstrip('/')

    xforms_iter = (
        XForm.objects.filter(require_auth=False)
        .values('id_string', 'user__username')
        .iterator(chunk_size=CHUNK_SIZE)
    )

    while True:
        xforms = list(islice(xforms_iter, CHUNK_SIZE))
        if not xforms:
            break
        keys = []
        for xform in xforms:
            username = xform['user__username']
            id_string = xform['id_string']
            keys.append(f"or:{parsed_url.netloc}/{username},{id_string}|{username}")

        lua_keys = '", "'.join(keys)

        lua_script = f"""
            local keys = {{"{lua_keys}"}}
            for _, key in ipairs(keys) do
                local redis_real_key = string.sub(key, 1, string.find(key, '|') - 1)
                local username = string.sub(key, string.find(key, '|') + 1, string.len(key))
                local ee_id = redis.call('get', redis_real_key)
                if ee_id then
                    redis.call('hset', 'id:' .. ee_id, 'openRosaServer', '{server_url}/' .. username)
                end
            end
        """
        redis_client = get_redis_connection('enketo_redis_main')
        pipeline = redis_client.pipeline()
        pipeline.eval(lua_script, 0)
        pipeline.execute()


def restore_require_auth_at_profile_level(apps, schema_editor):

    print(
        """
        You are migrating backwards from project-level control of anonymous
        submissions to account-level control.

        If you want to allow anonymous submissions again for existing accounts,
        you must enable that manually, either in the user profile settings UI
        of the KPI application, or by running commands in the KoboCAT Django
        shell to set `require_auth=False` on the `UserProfile` instances
        belonging to the desired accounts.
        """
    )

    # For those savvy enough to read the code here, offer an example of how to
    # set `require_auth=False` for all accounts having at least one *project*
    # that allowed anonymous submissions.
    # ⚠️ This is DANGEROUS because it potentially allows anonymous submissions
    # (and anonymous viewing of the form) for projects where it was *not*
    # previously allowed, e.g. an owner having 1 anonymous-allowed project and
    # 99 private ones would have all 100 projects exposed.
    #
    #     UserProfile.objects.filter(
    #         user_id__in=XForm.objects.filter(require_auth=False).values_list(
    #             'user_id'
    #         )
    #     ).update(require_auth=False)
    #     # Since `require_auth` at project level no longer does anything,
    #     # remove misleading values
    #     XForm.objects.filter(require_auth=True).update(require_auth=False)


def set_require_auth_at_project_level(apps, schema_editor):

    if settings.SKIP_HEAVY_MIGRATIONS:
        return

    print(
        """
        This migration might take a while. If it is too slow, you may want to
        re-run migrations with SKIP_HEAVY_MIGRATIONS=True and apply this one
        manually from the django shell.
        """
    )

    XForm = apps.get_model('logger', 'XForm')  # noqa
    UserProfile = apps.get_model('main', 'UserProfile')  # noqa

    XForm.objects.all().update(require_auth=True)
    XForm.objects.filter(
        user_id__in=UserProfile.objects.filter(require_auth=False).values_list(
            'user_id'
        )
    ).update(require_auth=False)


def update_open_rosa_server_in_redis(apps, schema_editor):

    if settings.SKIP_HEAVY_MIGRATIONS:
        return

    XForm = apps.get_model('logger', 'XForm')  # noqa

    parsed_url = urlparse(settings.KOBOCAT_URL)
    server_url = settings.KOBOCAT_URL.strip('/')

    xforms_iter = (
        XForm.objects.filter(require_auth=True)
        .values('id_string', 'user__username')
        .iterator(chunk_size=CHUNK_SIZE)
    )

    while True:
        xforms = list(islice(xforms_iter, CHUNK_SIZE))
        if not xforms:
            break
        keys = []
        for xform in xforms:
            username = xform['user__username']
            id_string = xform['id_string']
            keys.append(f"or:{parsed_url.netloc}/{username},{id_string}")

        lua_keys = '", "'.join(keys)

        lua_script = f"""
            local keys = {{"{lua_keys}"}}
            for _, key in ipairs(keys) do
                local ee_id = redis.call('get', key)
                if ee_id then
                    redis.call('hset', 'id:' .. ee_id, 'openRosaServer', '{server_url}')
                end
            end
        """
        redis_client = get_redis_connection('enketo_redis_main')
        pipeline = redis_client.pipeline()
        pipeline.eval(lua_script, 0)
        pipeline.execute()


class Migration(migrations.Migration):

    dependencies = [
        ('logger', '0033_add_deleted_at_field_to_attachment'),
    ]

    operations = [
        migrations.RunPython(
            set_require_auth_at_project_level,
            restore_require_auth_at_profile_level,
        ),
        migrations.RunPython(
            update_open_rosa_server_in_redis,
            restore_open_rosa_server_in_redis,
        ),
    ]
