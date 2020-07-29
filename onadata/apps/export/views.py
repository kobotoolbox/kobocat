# coding: utf-8

#################################################
# THIS APP IS DEAD CODE AND SHOULD BE EXCISED   #
# EVERY SINGLE ENDPOINT 500s EXCEPT export_menu #
#################################################

from __future__ import (unicode_literals, print_function, absolute_import,
                        division)

import uuid

from datetime import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, HttpResponseForbidden
from django.utils.translation import ugettext as _

from path import tempdir

from onadata.libs.utils.user_auth import has_permission

from formpack import FormPack


def readable_xform_required(func):
    def _wrapper(request, username, id_string):
        owner = get_object_or_404(User, username=username)
        xform = get_object_or_404(owner.xforms, id_string=id_string)
        if not has_permission(xform, owner, request):
            return HttpResponseForbidden(_(u'Not shared.'))
        return func(request, username, id_string)
    return _wrapper


def get_instances_for_user_and_form(user, form_id):
    userform_id = '{}_{}'.format(user, form_id)
    query = {'_userform_id': userform_id}
    return settings.MONGO_DB.instances.find(query)


def build_formpack(username, id_string):
    user = User.objects.get(username=username)
    xform = user.xforms.get(id_string=id_string)
    schema = {
        "id_string": id_string,
        "version": 'v1',
        "content": xform.to_kpi_content_schema(),
    }
    return FormPack([schema], id_string)


def build_export(request, username, id_string):

    hierarchy_in_labels = request.REQUEST.get(
        'hierarchy_in_labels', ''
    ).lower() == 'true'
    group_sep = request.REQUEST.get('groupsep', '/')
    lang = request.REQUEST.get('lang', None)

    options = {'versions': 'v1',
               'header_lang': lang,
               'group_sep': group_sep,
               'translation': lang,
               'hierarchy_in_labels': hierarchy_in_labels,
               'copy_fields': ('_id', '_uuid', '_submission_time'),
               'force_index': True}

    formpack = build_formpack(username, id_string)
    return formpack.export(**options)


def build_export_filename(export, extension):
    form_type = 'labels'
    if not export.translation:
        form_type = "values"
    elif export.translation != "_default":
        form_type = export.translation

    return "{title} - {form_type} - {date:%Y-%m-%d-%H-%M}.{ext}".format(
        form_type=form_type,
        date=datetime.utcnow(),
        title=export.title,
        ext=extension
    )


@readable_xform_required
def xlsx_export(request, username, id_string):

    export = build_export(request, username, id_string)
    data = [("v1", get_instances_for_user_and_form(username, id_string))]

    with tempdir() as d:
        tempfile = d / str(uuid.uuid4())
        export.to_xlsx(tempfile, data)
        xlsx = tempfile.bytes()

    name = build_export_filename(export, 'xlsx')
    ct = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    response = HttpResponse(xlsx, content_type=ct)
    response['Content-Disposition'] = 'attachment; filename="%s"' % name
    return response


@readable_xform_required
def csv_export(request, username, id_string):

    export = build_export(request, username, id_string)
    data = [("v1", get_instances_for_user_and_form(username, id_string))]

    name = build_export_filename(export, 'csv')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="%s"' % name

    for line in export.to_csv(data):
        response.write(line + "\n")

    return response

