# coding: utf-8
from __future__ import unicode_literals, print_function, division, absolute_import

import json
import logging
import os
import re
from datetime import datetime

import rest_framework.request
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage
from django.core.files.storage import get_storage_class
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import (
    HttpResponseForbidden, HttpResponseRedirect, HttpResponseNotFound,
    HttpResponseBadRequest, HttpResponse)
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.utils.http import urlquote
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_POST
from rest_framework.settings import api_settings

from onadata.apps.logger.models import XForm, Attachment
from onadata.apps.viewer.models.export import Export
from onadata.apps.viewer.tasks import create_async_export
from onadata.libs.exceptions import NoRecordsFoundError
from onadata.libs.utils.common_tags import SUBMISSION_TIME
from onadata.libs.utils.export_tools import (
    generate_export,
    should_create_new_export,
    kml_export_data,
    newset_export_for)
from onadata.libs.utils.image_tools import image_url
from onadata.libs.utils.log import audit_log, Actions
from onadata.libs.utils.logger_tools import response_with_mimetype_and_name, \
    disposition_ext_and_date
from onadata.libs.utils.user_auth import has_permission, \
    helper_auth_helper
from onadata.libs.utils.viewer_tools import export_def_from_filename

media_file_logger = logging.getLogger('media_files')


def _set_submission_time_to_query(query, request):
    query[SUBMISSION_TIME] = {}
    try:
        if request.GET.get('start'):
            query[SUBMISSION_TIME]['$gte'] = format_date_for_mongo(
                request.GET['start'])
        if request.GET.get('end'):
            query[SUBMISSION_TIME]['$lte'] = format_date_for_mongo(
                request.GET['end'])
    except ValueError:
        return HttpResponseBadRequest(
            _("Dates must be in the format YY_MM_DD_hh_mm_ss"))

    return query


def format_date_for_mongo(x):
    return datetime.strptime(x, '%y_%m_%d_%H_%M_%S')\
        .strftime('%Y-%m-%dT%H:%M:%S')


def data_export(request, username, id_string, export_type):
    owner = get_object_or_404(User, username__iexact=username)
    xform = get_object_or_404(XForm, id_string__exact=id_string, user=owner)
    helper_auth_helper(request)
    if not has_permission(xform, owner, request):
        return HttpResponseForbidden(_('Not shared.'))
    query = request.GET.get("query")
    extension = export_type

    # check if we should force xlsx
    force_xlsx = request.GET.get('xls') != 'true'
    if export_type == Export.XLS_EXPORT and force_xlsx:
        extension = 'xlsx'

    audit = {
        "xform": xform.id_string,
        "export_type": export_type
    }
    # check if we need to re-generate,
    # we always re-generate if a filter is specified
    if should_create_new_export(xform, export_type) or query or\
            'start' in request.GET or 'end' in request.GET:
        # check for start and end params
        if 'start' in request.GET or 'end' in request.GET:
            if not query:
                query = '{}'
            query = json.dumps(
                _set_submission_time_to_query(json.loads(query), request))
        try:
            export = generate_export(
                export_type, extension, username, id_string, None, query)
            audit_log(
                Actions.EXPORT_CREATED, request.user, owner,
                _("Created %(export_type)s export on '%(id_string)s'.") %
                {
                    'id_string': xform.id_string,
                    'export_type': export_type.upper()
                }, audit, request)
        except NoRecordsFoundError:
            return HttpResponseNotFound(_("No records found to export"))
    else:
        export = newset_export_for(xform, export_type)

    # log download as well
    audit_log(
        Actions.EXPORT_DOWNLOADED, request.user, owner,
        _("Downloaded %(export_type)s export on '%(id_string)s'.") %
        {
            'id_string': xform.id_string,
            'export_type': export_type.upper()
        }, audit, request)

    if not export.filename:
        # tends to happen when using newset_export_for.
        return HttpResponseNotFound("File does not exist!")

    # get extension from file_path, exporter could modify to
    # xlsx if it exceeds limits
    path, ext = os.path.splitext(export.filename)
    ext = ext[1:]
    if request.GET.get('raw'):
        id_string = None

    response = response_with_mimetype_and_name(
        Export.EXPORT_MIMES[ext], id_string, extension=ext,
        file_path=export.filepath)

    return response


@login_required
@require_POST
def create_export(request, username, id_string, export_type):
    owner = get_object_or_404(User, username__iexact=username)
    xform = get_object_or_404(XForm, id_string__exact=id_string, user=owner)
    if not has_permission(xform, owner, request):
        return HttpResponseForbidden(_('Not shared.'))

    query = request.POST.get("query")
    force_xlsx = request.POST.get('xls') != 'true'

    # export options
    group_delimiter = request.POST.get("options[group_delimiter]", '/')
    if group_delimiter not in ['.', '/']:
        return HttpResponseBadRequest(
            _("%s is not a valid delimiter" % group_delimiter))

    # default is True, so when dont_.. is yes
    # split_select_multiples becomes False
    split_select_multiples = request.POST.get(
        "options[dont_split_select_multiples]", "no") == "no"

    binary_select_multiples = getattr(settings, 'BINARY_SELECT_MULTIPLES',
                                      False)
    options = {
        'group_delimiter': group_delimiter,
        'split_select_multiples': split_select_multiples,
        'binary_select_multiples': binary_select_multiples,
    }

    try:
        create_async_export(xform, export_type, query, force_xlsx, options)
    except Export.ExportTypeError:
        return HttpResponseBadRequest(
            _("%s is not a valid export type" % export_type))
    else:
        audit = {
            "xform": xform.id_string,
            "export_type": export_type
        }
        audit_log(
            Actions.EXPORT_CREATED, request.user, owner,
            _("Created %(export_type)s export on '%(id_string)s'.") %
            {
                'export_type': export_type.upper(),
                'id_string': xform.id_string,
            }, audit, request)
        return HttpResponseRedirect(reverse(
            export_list,
            kwargs={
                "username": username,
                "id_string": id_string,
                "export_type": export_type
            })
        )


def export_list(request, username, id_string, export_type):
    try:
        Export.EXPORT_TYPE_DICT[export_type]
    except KeyError:
        return HttpResponseBadRequest(_('Invalid export type'))

    owner = get_object_or_404(User, username__iexact=username)
    xform = get_object_or_404(XForm, id_string__exact=id_string, user=owner)
    if not has_permission(xform, owner, request):
        return HttpResponseForbidden(_('Not shared.'))

    data = {
        'username': owner.username,
        'xform': xform,
        'export_type': export_type,
        'export_type_name': Export.EXPORT_TYPE_DICT[export_type],
        'exports': Export.objects.filter(
            xform=xform, export_type=export_type).order_by('-created_on')
    }

    return render(request, 'export_list.html', data)


def export_progress(request, username, id_string, export_type):
    owner = get_object_or_404(User, username__iexact=username)
    xform = get_object_or_404(XForm, id_string__exact=id_string, user=owner)
    if not has_permission(xform, owner, request):
        return HttpResponseForbidden(_('Not shared.'))

    # find the export entry in the db
    export_ids = request.GET.getlist('export_ids')
    exports = Export.objects.filter(xform=xform, id__in=export_ids)
    statuses = []
    for export in exports:
        status = {
            'complete': False,
            'url': None,
            'filename': None,
            'export_id': export.id
        }

        if export.status == Export.SUCCESSFUL:
            status['url'] = reverse(export_download, kwargs={
                'username': owner.username,
                'id_string': xform.id_string,
                'export_type': export.export_type,
                'filename': export.filename
            })
            status['filename'] = export.filename

        # mark as complete if it either failed or succeeded but NOT pending
        if export.status == Export.SUCCESSFUL or export.status == Export.FAILED:
            status['complete'] = True
        statuses.append(status)

    return HttpResponse(
        json.dumps(statuses), content_type='application/json')


def export_download(request, username, id_string, export_type, filename):
    owner = get_object_or_404(User, username__iexact=username)
    xform = get_object_or_404(XForm, id_string__exact=id_string, user=owner)
    helper_auth_helper(request)
    if not has_permission(xform, owner, request):
        return HttpResponseForbidden(_('Not shared.'))

    # find the export entry in the db
    export = get_object_or_404(Export, xform=xform, filename=filename)

    ext, mime_type = export_def_from_filename(export.filename)

    audit = {
        "xform": xform.id_string,
        "export_type": export.export_type
    }
    audit_log(
        Actions.EXPORT_DOWNLOADED, request.user, owner,
        _("Downloaded %(export_type)s export '%(filename)s' "
          "on '%(id_string)s'.") %
        {
            'export_type': export.export_type.upper(),
            'filename': export.filename,
            'id_string': xform.id_string,
        }, audit, request)
    if request.GET.get('raw'):
        id_string = None

    default_storage = get_storage_class()()
    if not isinstance(default_storage, FileSystemStorage):
        return HttpResponseRedirect(default_storage.url(export.filepath))

    basename = os.path.splitext(export.filename)[0]
    response = response_with_mimetype_and_name(
        mime_type, name=basename, extension=ext,
        file_path=export.filepath, show_date=False)
    return response


@login_required
@require_POST
def delete_export(request, username, id_string, export_type):
    owner = get_object_or_404(User, username__iexact=username)
    xform = get_object_or_404(XForm, id_string__exact=id_string, user=owner)
    if not has_permission(xform, owner, request):
        return HttpResponseForbidden(_('Not shared.'))

    export_id = request.POST.get('export_id')

    # find the export entry in the db
    export = get_object_or_404(Export, id=export_id)

    export.delete()
    audit = {
        "xform": xform.id_string,
        "export_type": export.export_type
    }
    audit_log(
        Actions.EXPORT_DOWNLOADED, request.user, owner,
        _("Deleted %(export_type)s export '%(filename)s'"
          " on '%(id_string)s'.") %
        {
            'export_type': export.export_type.upper(),
            'filename': export.filename,
            'id_string': xform.id_string,
        }, audit, request)
    return HttpResponseRedirect(reverse(
        export_list,
        kwargs={
            "username": username,
            "id_string": id_string,
            "export_type": export_type
        }))


def kml_export(request, username, id_string):
    # read the locations from the database
    owner = get_object_or_404(User, username__iexact=username)
    xform = get_object_or_404(XForm, id_string__exact=id_string, user=owner)
    helper_auth_helper(request)
    if not has_permission(xform, owner, request):
        return HttpResponseForbidden(_('Not shared.'))
    data = {'data': kml_export_data(id_string, user=owner)}
    response = \
        render(request, "survey.kml", data,
               content_type="application/vnd.google-earth.kml+xml")
    response['Content-Disposition'] = \
        disposition_ext_and_date(id_string, 'kml')
    audit = {
        "xform": xform.id_string,
        "export_type": Export.KML_EXPORT
    }
    audit_log(
        Actions.EXPORT_CREATED, request.user, owner,
        _("Created KML export on '%(id_string)s'.") %
        {
            'id_string': xform.id_string,
        }, audit, request)
    # log download as well
    audit_log(
        Actions.EXPORT_DOWNLOADED, request.user, owner,
        _("Downloaded KML export on '%(id_string)s'.") %
        {
            'id_string': xform.id_string,
        }, audit, request)

    return response


def attachment_url(request, size='medium'):
    media_file = request.GET.get('media_file')
    # TODO: how to make sure we have the right media file,
    # this assumes duplicates are the same file.
    #
    # Django seems to already handle that. It appends datetime to the filename.
    # It means duplicated would be only for the same user who uploaded two files
    # with same name at the same second.
    if media_file:
        # Strip out garbage (cache buster?) added by Galleria.js
        media_file = media_file.split('?')[0]
        mtch = re.search(r'^([^/]+)/attachments/([^/]+)$', media_file)
        if mtch:
            # in cases where the media_file url created by instance.html's
            # _attachment_url function is in the wrong format, this will
            # match attachments with the correct owner and the same file name
            (username, filename) = mtch.groups()
            result = Attachment.objects.filter(
                    instance__xform__user__username=username,
                ).filter(
                    Q(media_file_basename=filename) | Q(
                        media_file_basename=None,
                        media_file__endswith='/' + filename
                    )
                )[0:1]
        else:
            # search for media_file with exact matching name
            result = Attachment.objects.filter(media_file=media_file)[0:1]

        try:
            attachment = result[0]
        except IndexError:
            media_file_logger.info('attachment not found')
            return HttpResponseNotFound(_('Attachment not found'))

        # Checks whether users are allowed to see the media file before giving them
        # the url
        xform = attachment.instance.xform

        if not request.user.is_authenticated():
            # This is not a DRF view, but we need to honor things like
            # `DigestAuthentication` (ODK Briefcase uses it!) and
            # `TokenAuthentication`. Let's try all the DRF authentication
            # classes before giving up
            drf_request = rest_framework.request.Request(request)
            for auth_class in api_settings.DEFAULT_AUTHENTICATION_CLASSES:
                auth_tuple = auth_class().authenticate(drf_request)
                if auth_tuple is not None:
                    # Is it kosher to modify `request`? Let's do it anyway
                    # since that's what `has_permission()` requires...
                    request.user = auth_tuple[0]
                    # `DEFAULT_AUTHENTICATION_CLASSES` are ordered and the
                    # first match wins; don't look any further
                    break

        if not has_permission(xform, xform.user, request):
            return HttpResponseForbidden(_('Not shared.'))

        media_url = None

        if not attachment.mimetype.startswith('image'):
            media_url = attachment.media_file.url
        else:
            try:
                media_url = image_url(attachment, size)
            except:
                media_file_logger.error('could not get thumbnail for image', exc_info=True)

        if media_url:
            # We want nginx to serve the media (instead of redirecting the media itself)
            # PROS:
            # - It avoids revealing the real location of the media.
            # - Full control on permission
            # CONS:
            # - When using S3 Storage, traffic is multiplied by 2.
            #    S3 -> Nginx -> User
            response = HttpResponse()
            default_storage = get_storage_class()()
            if not isinstance(default_storage, FileSystemStorage):
                # Double-encode the S3 URL to take advantage of NGINX's
                # otherwise troublesome automatic decoding
                protected_url = '/protected-s3/{}'.format(urlquote(media_url))
            else:
                protected_url = media_url.replace(settings.MEDIA_URL, "/protected/")

            # Let nginx determine the correct content type
            response["Content-Type"] = ""
            response["X-Accel-Redirect"] = protected_url
            return response

    return HttpResponseNotFound(_('Error: Attachment not found'))
