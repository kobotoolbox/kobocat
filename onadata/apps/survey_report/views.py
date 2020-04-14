# coding: utf-8
from __future__ import unicode_literals, print_function, division, absolute_import

import uuid

from datetime import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseForbidden, Http404, QueryDict
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse

from pure_pagination import Paginator, EmptyPage, PageNotAnInteger

from path import tempdir

from onadata.libs.utils.user_auth import has_permission

from formpack import FormPack


def readable_xform_required(func):
    def _wrapper(request, username, id_string, *args, **kwargs):
        owner = get_object_or_404(User, username=username)
        xform = get_object_or_404(owner.xforms, id_string=id_string)
        if not has_permission(xform, owner, request):
            return HttpResponseForbidden(_('Not shared.'))
        return func(request, username, id_string, *args, **kwargs)
    return _wrapper


def get_instances_for_user_and_form(user, form_id, submission=None):
    userform_id = '{}_{}'.format(user, form_id)
    query = {'_userform_id': userform_id, '_deleted_at': {'$exists': False}}
    if submission:
        query['_id'] = submission
    return settings.MONGO_DB.instances.find(query)


def build_formpack(username, id_string):
    user = User.objects.get(username=username)
    xform = user.xforms.get(id_string=id_string)
    schema = {
        "id_string": id_string,
        "version": 'v1',
        "content": xform.to_kpi_content_schema(),
    }
    return user, xform, FormPack([schema], xform.title)


def build_export_context(request, username, id_string):

    hierarchy_in_labels = request.REQUEST.get(
        'hierarchy_in_labels', ''
    ).lower() in ('true', 'on')
    group_sep = request.REQUEST.get('group_sep', '/')

    user, xform, formpack = build_formpack(username, id_string)

    translations = formpack.available_translations
    lang = request.REQUEST.get('lang', None) or next(iter(translations), None)

    options = {'versions': 'v1',
               'group_sep': group_sep,
               'lang': lang,
               'hierarchy_in_labels': hierarchy_in_labels,
               'copy_fields': ('_id', '_uuid', '_submission_time'),
               'force_index': True
               }

    return {
        'username': username,
        'id_string': id_string,
        'languages': translations,
        'headers_lang': lang,
        'formpack': formpack,
        'xform': xform,
        'group_sep': group_sep,
        'lang': lang,
        'hierarchy_in_labels': hierarchy_in_labels,
        'export': formpack.export(**options)
    }


def build_export_filename(export, extension):
    form_type = 'labels'
    if not export.lang:
        form_type = "values"
    elif export.lang != "_default":
        form_type = export.lang

    return "{title} - {form_type} - {date:%Y-%m-%d-%H-%M}.{ext}".format(
        form_type=form_type,
        date=datetime.utcnow(),
        title=export.title,
        ext=extension
    )


@readable_xform_required
def export_menu(request, username, id_string):

    req = request.REQUEST
    export_type = req.get('type', None)
    if export_type:
        q = QueryDict('', mutable=True)
        q['lang'] = req.get('lang')
        q['hierarchy_in_labels'] = req.get('hierarchy_in_labels')
        q['group_sep'] = req.get('group_sep', '/')

        if export_type == "xlsx":
            url = reverse('formpack_xlsx_export', args=(username, id_string))
            return redirect(url + '?' + q.urlencode())
        if export_type == "csv":
            url = reverse('formpack_csv_export', args=(username, id_string))
            return redirect(url + '?' + q.urlencode())

    context = build_export_context(request, username, id_string)
    return render(request, 'survey_report/export_menu.html', context)


@readable_xform_required
def autoreport_menu(request, username, id_string):

    user, xform, form_pack = build_formpack(username, id_string)

    # exclude fields in repeat group
    split_by_fields = form_pack.get_fields_for_versions(data_types="select_one")

    context = {
        'languages': form_pack.available_translations,
        'username': username,
        'id_string': id_string,
        'split_by_fields': split_by_fields
    }

    return render(request, 'survey_report/autoreport_menu.html', context)


@readable_xform_required
def xlsx_export(request, username, id_string):

    export = build_export_context(request, username, id_string)['export']
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

    export = build_export_context(request, username, id_string)['export']
    data = [("v1", get_instances_for_user_and_form(username, id_string))]

    name = build_export_filename(export, 'csv')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="%s"' % name

    for line in export.to_csv(data):
        response.write(line + "\n")

    return response


@readable_xform_required
def html_export(request, username, id_string):

    limit = int(request.REQUEST.get('limit', 100))

    cursor = get_instances_for_user_and_form(username, id_string)
    paginator = Paginator(cursor, limit, request=request)

    try:
        page = paginator.page(request.REQUEST.get('page', 1))
    except (EmptyPage, PageNotAnInteger):
        try:
            page = paginator.page(1)
        except (EmptyPage, PageNotAnInteger):
            raise Http404('This report has no submissions')

    data = [("v1", page.object_list)]
    context = build_export_context(request, username, id_string)

    context.update({
        'page': page,
        'table': [],
        'title': id_string,
    })

    export = context['export']
    sections = list(export.labels.items())
    section, labels = sections[0]
    id_index = labels.index('_id')

    # generator dublicating the "_id" to allow to make a link to each
    # submission
    def make_table(submissions):
        for chunk in export.parse_submissions(submissions):
            for section_name, rows in chunk.items():
                if section == section_name:
                    for row in rows:
                        yield row[id_index], row

    context['labels'] = labels
    context['data'] = make_table(data)

    return render(request, 'survey_report/export_html.html', context)


@readable_xform_required
def auto_report(request, username, id_string):

    user, xform, formpack = build_formpack(username, id_string)
    report = formpack.autoreport()

    limit = int(request.REQUEST.get('limit', 20))
    split_by = request.REQUEST.get('split_by') or None

    fields = [field.name for field in formpack.get_fields_for_versions()]
    paginator = Paginator(fields, limit, request=request)

    try:
        page = paginator.page(request.REQUEST.get('page', 1))
    except (EmptyPage, PageNotAnInteger):
        try:
            page = paginator.page(1)
        except (EmptyPage, PageNotAnInteger):
            raise Http404('This report has no submissions')

    # remove fields in a group
    split_by_fields = formpack.get_fields_for_versions(data_types="select_one")
    translations = formpack.available_translations
    lang = request.REQUEST.get('lang', None) or next(iter(translations), None)

    ctx = {
        'page': page,
        'stats': [],
        'title': xform.title,
        'split_by': split_by,
        'split_by_fields': split_by_fields,
        'username': username,
        'id_string': id_string,
        'languages': translations,
        'headers_lang': lang,
        'xform': xform
    }

    data = [("v1", get_instances_for_user_and_form(username, id_string))]
    ctx['stats'] = report.get_stats(data, page.object_list, lang, split_by)

    if split_by:

        return render(request, 'survey_report/auto_report_split_by.html', ctx)

    return render(request, 'survey_report/auto_report.html', ctx)


@readable_xform_required
def view_one_submission(request, username, id_string, submission):

    submission = int(submission)
    instances = get_instances_for_user_and_form(username, id_string, submission)
    instances = list(instances)
    if not instances:
        raise Http404('Unable to find this submission')

    context = {
        'title': id_string
    }

    data = [("v1", instances)]
    export = build_export_context(request, username, id_string)['export']
    submission = next(iter(export.to_dict(data).values()))
    context['submission'] = zip(submission['fields'], submission['data'][0])

    return render(request, 'survey_report/view_submission.html', context)
