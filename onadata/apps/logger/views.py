# coding: utf-8
import json
import os
import tempfile
import re
from datetime import datetime, date

from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.files.storage import get_storage_class
from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    HttpResponseRedirect,
    StreamingHttpResponse,
    Http404,
)
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.template import loader
from django.utils.six import text_type
from django.utils.translation import gettext as t
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

from onadata.apps.main.models import UserProfile
from onadata.apps.logger.import_tools import import_instances_from_zip
from onadata.apps.logger.models.xform import XForm
from onadata.libs.authentication import digest_authentication
from onadata.libs.utils.log import audit_log, Actions
from onadata.libs.utils.logger_tools import BaseOpenRosaResponse
from onadata.libs.utils.logger_tools import response_with_mimetype_and_name
from onadata.libs.utils.user_auth import (
    helper_auth_helper,
    has_permission,
    add_cors_headers,
)
from .tasks import generate_stats_zip
from ...koboform.pyxform_utils import convert_csv_to_xls

IO_ERROR_STRINGS = [
    'request data read error',
    'error during read(65536) on wsgi.input'
]


def _bad_request(e):
    strerror = text_type(e)

    return strerror and strerror in IO_ERROR_STRINGS


def _extract_uuid(text):
    text = text[text.find("@key="):-1].replace("@key=", "")
    if text.startswith("uuid:"):
        text = text.replace("uuid:", "")
    return text


def _parse_int(num):
    try:
        return num and int(num)
    except ValueError:
        pass


def _submission_response(request, instance):
    data = {
        'message': t("Successful submission."),
        'formid': instance.xform.id_string,
        'encrypted': instance.xform.encrypted,
        'instanceID': f'uuid:{instance.uuid}',
        'submissionDate': instance.date_created.isoformat(),
        'markedAsCompleteDate': instance.date_modified.isoformat()
    }

    t = loader.get_template('submission.xml')

    return BaseOpenRosaResponse(t.render(data, request=request))


@require_POST
@csrf_exempt
def bulksubmission(request, username):
    # puts it in a temp directory.
    # runs "import_tools(temp_directory)"
    # deletes
    posting_user = get_object_or_404(User, username__iexact=username)

    # request.FILES is a django.utils.datastructures.MultiValueDict
    # for each key we have a list of values
    try:
        temp_postfile = request.FILES.pop("zip_submission_file", [])
    except IOError:
        return HttpResponseBadRequest(t("There was a problem receiving your "
                                        "ODK submission. [Error: IO Error "
                                        "reading data]"))
    if len(temp_postfile) != 1:
        return HttpResponseBadRequest(t("There was a problem receiving your"
                                        " ODK submission. [Error: multiple "
                                        "submission files (?)]"))

    postfile = temp_postfile[0]
    tempdir = tempfile.gettempdir()
    our_tfpath = os.path.join(tempdir, postfile.name)

    with open(our_tfpath, 'wb') as f:
        f.write(postfile.read())

    with open(our_tfpath, 'rb') as f:
        total_count, success_count, errors = import_instances_from_zip(
            f, posting_user)
    # chose the try approach as suggested by the link below
    # http://stackoverflow.com/questions/82831
    try:
        os.remove(our_tfpath)
    except IOError:
        # TODO: log this Exception somewhere
        pass
    json_msg = {
        'message': t("Submission complete. Out of %(total)d "
                     "survey instances, %(success)d were imported, "
                     "(%(rejected)d were rejected as duplicates, "
                     "missing forms, etc.)") %
        {'total': total_count, 'success': success_count,
         'rejected': total_count - success_count},
        'errors': "%d %s" % (len(errors), errors)
    }
    audit = {
        "bulk_submission_log": json_msg
    }
    audit_log(Actions.USER_BULK_SUBMISSION, request.user, posting_user,
              t("Made bulk submissions."), audit, request)
    response = HttpResponse(json.dumps(json_msg))
    response.status_code = 200
    response['Location'] = request.build_absolute_uri(request.path)
    return response


@login_required
def bulksubmission_form(request, username=None):
    username = username if username is None else username.lower()
    if request.user.username == username:
        return render(request, 'bulk_submission_form.html')
    else:
        return HttpResponseRedirect('/%s' % request.user.username)


def download_xform(request, username, id_string):
    user = get_object_or_404(User, username__iexact=username)
    xform = get_object_or_404(XForm,
                              user=user, id_string__exact=id_string)
    profile, created = UserProfile.objects.get_or_create(user=user)

    if (
        profile.require_auth
        and (digest_response := digest_authentication(request))
    ):
        return digest_response

    audit = {
        "xform": xform.id_string
    }
    audit_log(
        Actions.FORM_XML_DOWNLOADED, request.user, xform.user,
        t("Downloaded XML for form '%(id_string)s'.") %
        {
            "id_string": xform.id_string
        }, audit, request)
    response = response_with_mimetype_and_name('xml', id_string,
                                               show_date=False)
    response.content = xform.xml
    return response


def download_xlsform(request, username, id_string):
    xform = get_object_or_404(XForm,
                              user__username__iexact=username,
                              id_string__exact=id_string)
    owner = User.objects.get(username__iexact=username)
    helper_auth_helper(request)

    if not has_permission(xform, owner, request, xform.shared):
        return HttpResponseForbidden('Not shared.')

    file_path = xform.xls.name
    default_storage = get_storage_class()()

    if file_path != '' and default_storage.exists(file_path):
        audit = {
            "xform": xform.id_string
        }
        audit_log(
            Actions.FORM_XLS_DOWNLOADED, request.user, xform.user,
            t("Downloaded XLS file for form '%(id_string)s'.") %
            {
                "id_string": xform.id_string
            }, audit, request)

        if file_path.endswith('.csv'):
            with default_storage.open(file_path) as ff:
                xls_io = convert_csv_to_xls(ff.read())
                response = StreamingHttpResponse(
                    xls_io, content_type='application/vnd.ms-excel; charset=utf-8')
                response[
                    'Content-Disposition'] = 'attachment; filename=%s.xls' % xform.id_string
                return response

        split_path = file_path.split(os.extsep)
        extension = 'xls'

        if len(split_path) > 1:
            extension = split_path[len(split_path) - 1]

        response = response_with_mimetype_and_name(
            'vnd.ms-excel', id_string, show_date=False, extension=extension,
            file_path=file_path)

        return response

    else:
        messages.add_message(request, messages.WARNING,
                             t('No XLS file for your form '
                               '<strong>%(id)s</strong>')
                             % {'id': id_string})

        return HttpResponseRedirect("/%s" % username)


def download_jsonform(request, username, id_string):
    owner = get_object_or_404(User, username__iexact=username)
    xform = get_object_or_404(XForm, user__username__iexact=username,
                              id_string__exact=id_string)
    if request.method == "OPTIONS":
        response = HttpResponse()
        add_cors_headers(response)
        return response
    helper_auth_helper(request)
    if not has_permission(xform, owner, request, xform.shared):
        response = HttpResponseForbidden(t('Not shared.'))
        add_cors_headers(response)
        return response
    response = response_with_mimetype_and_name('json', id_string,
                                               show_date=False)
    if 'callback' in request.GET and request.GET.get('callback') != '':
        callback = request.GET.get('callback')
        response.content = "%s(%s)" % (callback, xform.json)
    else:
        add_cors_headers(response)
        response.content = xform.json
    return response


@user_passes_test(lambda u: u.is_superuser)
def superuser_stats(request, username):
    base_filename = '{}_{}_{}.zip'.format(
        re.sub('[^a-zA-Z0-9]', '-', request.get_host()),
        date.today(),
        datetime.now().microsecond
    )
    filename = os.path.join(
        request.user.username,
        'superuser_stats',
        base_filename
    )
    generate_stats_zip.delay(filename)
    template_ish = (
        '<html><head><title>Hello, superuser.</title></head>'
        '<body>Your report is being generated. Once finished, it will be '
        'available at <a href="{0}">{0}</a>. If you receive a 404, please '
        'refresh your browser periodically until your request succeeds.'
        '</body></html>'
    ).format(base_filename)
    return HttpResponse(template_ish)


@user_passes_test(lambda u: u.is_superuser)
def retrieve_superuser_stats(request, username, base_filename):
    filename = os.path.join(
        request.user.username,
        'superuser_stats',
        base_filename
    )
    default_storage = get_storage_class()()
    if not default_storage.exists(filename):
        raise Http404
    with default_storage.open(filename) as f:
        response = StreamingHttpResponse(f, content_type='application/zip')
        response['Content-Disposition'] = 'attachment;filename="{}"'.format(
            base_filename)
        return response
