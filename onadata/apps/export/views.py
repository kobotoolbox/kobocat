# coding: utf-8

from __future__ import (unicode_literals, print_function, absolute_import,
                        division)

import json
import uuid

from datetime import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.shortcuts import render
from django.http import HttpResponse
from django.utils.safestring import mark_safe

from pure_pagination import Paginator, EmptyPage, PageNotAnInteger

from path import tempdir

from onadata.apps.logger.models import XForm

from formpack import FormPack


def get_instances_for_user_and_form(user, form_id):
    userform_id = '{}_{}'.format(user, form_id)
    query = {'_userform_id': userform_id}
    return settings.MONGO_DB.instances.find(query)


def export_menu(request, username, id_string):

    user = User.objects.get(username=username) 
    xform = user.xforms.get(id_string=id_string)
    schema = {
        "id_string": id_string,
        "version": 'v1',
        "content": xform.to_kpi_content_schema(),
    }

    form_pack = FormPack([schema], id_string)

    context = {
        'languages': form_pack.available_translations,
        'username': username,
        'id_string': id_string
    }

    return render(request, 'export/export_menu.html', context)


def xlsx_export(request, username, id_string):

    hierarchy_in_labels = request.REQUEST.get('hierarchy_in_labels', None)
    group_sep = request.REQUEST.get('groupsep', '/')
    lang = request.REQUEST.get('lang', None)

    user = User.objects.get(username=username) 
    xform = user.xforms.get(id_string=id_string)
    schema = {
        "id_string": id_string,
        "version": 'v1',
        "content": xform.to_kpi_content_schema(),
    }

    data = [("v1", get_instances_for_user_and_form(username, id_string))]
    options = {'versions': 'v1', 
               'header_lang': lang,
               'group_sep': group_sep,
               'translation': lang, 
               'hierarchy_in_labels': hierarchy_in_labels,
               'copy_fields': ('_id', '_uuid', '_submission_time'),
               'force_index': True}
    export = FormPack([schema], id_string).export(**options)

    with tempdir() as d:
        tempfile = d / str(uuid.uuid4())
        export.to_xlsx(tempfile, data)
        xlsx = tempfile.bytes()
  
    form_type = 'labels'
    if not lang:
        form_type = "values"
    elif lang != "_default":
        form_type = lang
    name = "{title} - {form_type} - {date:%Y-%m-%d-%H-%M}.xlsx".format(
        form_type=form_type,
        date=datetime.utcnow(),
        title=xform.title,
    )

    ct = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    
    response = HttpResponse(xlsx, content_type=ct)
    response['Content-Disposition'] = 'attachment; filename="%s"' % name
    return response


def csv_export(request, username, id_string):

    hierarchy_in_labels = request.REQUEST.get('hierarchy_in_labels', None)
    group_sep = request.REQUEST.get('groupsep', '/')
    lang = request.REQUEST.get('lang', None)

    user = User.objects.get(username=username) 
    xform = user.xforms.get(id_string=id_string)
    schema = {
        "id_string": id_string,
        "version": 'v1',
        "content": xform.to_kpi_content_schema(),
    }

    data = [("v1", get_instances_for_user_and_form(username, id_string))]
    options = {'versions': 'v1', 
               'header_lang': lang,
               'group_sep': group_sep,
               'translation': lang, 
               'hierarchy_in_labels': hierarchy_in_labels,
               'copy_fields': ('_id', '_uuid', '_submission_time'),
               'force_index': True}
    export = FormPack([schema], id_string).export(**options)

    form_type = 'labels'
    if not lang:
        form_type = "values"
    elif lang != "_default":
        form_type = lang
    name = "{title} - {form_type} - {date:%Y-%m-%d-%H-%M}.csv".format(
        form_type=form_type,
        date=datetime.utcnow(),
        title=xform.title,
    )
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="%s"' % name

    for line in export.to_csv(data):
        response.write(line + "\n")

    return response



def html_export(request, username, id_string):

    hierarchy_in_labels = request.REQUEST.get('hierarchy_in_labels', None)
    group_sep = request.REQUEST.get('groupsep', '/')
    lang = request.REQUEST.get('lang', None)
    limit = request.REQUEST.get('limit', 100)

    cursor = get_instances_for_user_and_form(username, id_string)
    paginator = Paginator(cursor, limit, request=request)

    try:
        page = paginator.page(request.REQUEST.get('page', 1))
    except (EmptyPage, PageNotAnInteger):
        try:
            page = paginator.page(1)
        except (EmptyPage, PageNotAnInteger):
            page = None

    context = {
        'page': page,
        'table': []
    }

    if page:
     
        user = User.objects.get(username=username) 
        xform = user.xforms.get(id_string=id_string)
        schema = {
            "id_string": id_string,
            "version": 'v1',
            "content": xform.to_kpi_content_schema(),
        }

        data = [("v1", page.object_list)]
        options = {'versions': 'v1', 
                   'header_lang': lang,
                   'group_sep': group_sep,
                   'translation': lang, 
                   'hierarchy_in_labels': hierarchy_in_labels,
                   'copy_fields': ('_id', '_uuid', '_submission_time'),
                   'force_index': True}
        export = FormPack([schema], id_string).export(**options)
        context['table'] = mark_safe("\n".join(export.to_html(data)))
        context['title'] = id_string

    return render(request, 'export/export_html.html', context)

