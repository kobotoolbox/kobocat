# coding: utf-8
import os

import requests
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.urls import reverse
from django.http import HttpResponseForbidden
from django.http import HttpResponseNotFound
from django.http import HttpResponseRedirect
from django.http import HttpResponseServerError
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as t

from onadata.apps.logger.models import XForm
from onadata.apps.main.models import MetaData
from onadata.libs.utils.log import audit_log, Actions
from onadata.libs.utils.logger_tools import (
    check_submission_permissions,
    response_with_mimetype_and_name,
)


def download_media_data(request, username, id_string, data_id):
    xform = get_object_or_404(
        XForm, user__username__iexact=username,
        id_string__exact=id_string)
    owner = xform.user
    data = get_object_or_404(MetaData, id=data_id)

    if request.GET.get('del', False):
        if username == request.user.username:
            try:
                # ensure filename is not an empty string
                if data.data_file.name != '':
                    default_storage.delete(data.data_file.name)

                data.delete()
                audit = {
                    'xform': xform.id_string
                }
                audit_log(
                    Actions.FORM_UPDATED, request.user, owner,
                    t("Media download '%(filename)s' deleted from "
                        "'%(id_string)s'.") %
                    {
                        'id_string': xform.id_string,
                        'filename': os.path.basename(data.data_file.name)
                    }, audit, request)
                if (
                    'HTTP_REFERER' in request.META
                    and request.META['HTTP_REFERER'].strip()
                ):
                    return HttpResponseRedirect(request.META['HTTP_REFERER'])

                return HttpResponseRedirect(reverse(show, kwargs={
                    'username': username,
                    'id_string': id_string
                }))
            except Exception as e:
                return HttpResponseServerError(e)
    else:
        if not xform.shared:
            # raise an exception if the requesting user is not allowed to
            # submit to this form (and therefore should not see this form media)
            check_submission_permissions(request, xform)

        if data.data_file.name == '' and data.data_value is not None:
            return HttpResponseRedirect(data.data_value)

        file_path = data.data_file.name
        filename, extension = os.path.splitext(file_path.split('/')[-1])
        extension = extension.strip('.')
        if default_storage.exists(file_path):
            audit = {
                'xform': xform.id_string
            }
            audit_log(
                Actions.FORM_UPDATED, request.user, owner,
                t("Media '%(filename)s' downloaded from "
                    "'%(id_string)s'.") %
                {
                    'id_string': xform.id_string,
                    'filename': os.path.basename(file_path)
                }, audit, request)
            response = response_with_mimetype_and_name(
                data.data_file_type,
                filename, extension=extension, show_date=False,
                file_path=file_path)
            return response
        else:
            return HttpResponseNotFound()

    return HttpResponseForbidden(t('Permission denied.'))


def _make_authenticated_request(request, user):
    """
    Make an authenticated request to KPI using the current session.
    Returns response from KPI.
    """
    return requests.get(
        url=_get_migrate_url(user.username),
        cookies={settings.SESSION_COOKIE_NAME: request.session.session_key}
    )


def _get_migrate_url(username):
    return '{kf_url}/api/v2/users/{username}/migrate/'.format(
        kf_url=settings.KOBOFORM_URL, username=username
    )
