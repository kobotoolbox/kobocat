# coding: utf-8
import os

from bson import json_util
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.files.storage import get_storage_class
from django.urls import reverse
from django.http import HttpResponse
from django.http import HttpResponseBadRequest
from django.http import HttpResponseForbidden
from django.http import HttpResponseNotFound
from django.http import HttpResponseRedirect
from django.http import HttpResponseServerError
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_GET
from django.views.decorators.http import require_http_methods
from rest_framework.authtoken.models import Token
from rest_framework import status
from ssrf_protect.ssrf_protect import SSRFProtect, SSRFProtectException

from onadata.apps.logger.models import XForm
from onadata.apps.main.forms import (
    MediaForm,
)
from onadata.apps.main.forms import QuickConverterForm
from onadata.apps.main.models import UserProfile, MetaData
from onadata.apps.viewer.models.parsed_instance import ParsedInstance
from onadata.libs.utils.log import audit_log, Actions
from onadata.libs.utils.logger_tools import response_with_mimetype_and_name
from onadata.libs.utils.user_auth import (
    add_cors_headers,
    check_and_set_user_and_form,
    get_xform_and_perms,
    helper_auth_helper,
    set_profile_data,
)


def home(request):
    if request.user.username:
        return HttpResponseRedirect(
            reverse(profile, kwargs={'username': request.user.username}))

    return render(request, 'home.html')


@login_required
def login_redirect(request):
    return HttpResponseRedirect(reverse(profile,
                                kwargs={'username': request.user.username}))


def profile(request, username):
    content_user = get_object_or_404(User, username__iexact=username)
    form = QuickConverterForm()
    data = {'form': form}

    # If the "Sync XForms" button is pressed in the UI, a call to KPI's
    # `/migrate` endpoint is made to sync kobocat and KPI.
    if request.GET.get('sync_xforms') == 'true':
        migrate_response = _make_authenticated_request(request, content_user)
        message = {}
        if migrate_response.status_code == status.HTTP_200_OK:
            message['text'] = _(
                'The migration process has started, please check the '
                'project list in the <a href={}>new interface</a> and ensure '
                'your projects have synced.'
            ).format(settings.KOBOFORM_URL)
        else:
            message['text'] = _(
                'Something went wrong trying to migrate your forms. Please try '
                'again or reach out on the <a'
                'href="https://community.kobotoolbox.org/">community forum</a> '
                'for assistance.'
            )

        data['message'] = message

    # profile view...
    # for the same user -> dashboard
    if content_user == request.user:
        show_dashboard = True
        all_forms = content_user.xforms.count()

        request_url = request.build_absolute_uri(
            "/%s" % request.user.username)
        url = request_url.replace('http://', 'https://')
        xforms = XForm.objects.filter(user=content_user)\
            .select_related('user', 'instances')

        user_xforms = xforms
        # forms shared with user
        xfct = ContentType.objects.get(app_label='logger', model='xform')
        xfs = content_user.userobjectpermission_set.filter(content_type=xfct)
        shared_forms_pks = list(set([xf.object_pk for xf in xfs]))
        forms_shared_with = XForm.objects.filter(
            pk__in=shared_forms_pks).exclude(user=content_user)\
            .select_related('user')
        # all forms to which the user has access
        published_or_shared = XForm.objects.filter(
            pk__in=shared_forms_pks).select_related('user')
        xforms_list = [
            {
                'id': 'published',
                'xforms': user_xforms,
                'title': _("Published Forms"),
                'small': _("Export, map, and view submissions.")
            },
            {
                'id': 'shared',
                'xforms': forms_shared_with,
                'title': _("Shared Forms"),
                'small': _("List of forms shared with you.")
            },
            {
                'id': 'published_or_shared',
                'xforms': published_or_shared,
                'title': _("Published Forms"),
                'small': _("Export, map, and view submissions.")
            }
        ]
        data.update({
            'all_forms': all_forms,
            'show_dashboard': show_dashboard,
            'form': form,
            'url': url,
            'user_xforms': user_xforms,
            'xforms_list': xforms_list,
            'forms_shared_with': forms_shared_with
        })
    # for any other user -> profile
    set_profile_data(data, content_user)

    return render(request, "profile.html", data)


def redirect_to_public_link(request, uuid):
    xform = get_object_or_404(XForm, uuid=uuid)
    request.session['public_link'] = \
        xform.uuid if MetaData.public_link(xform) else False

    return HttpResponseRedirect(reverse(show, kwargs={
        'username': xform.user.username,
        'id_string': xform.id_string
    }))


@require_GET
def show(request, username=None, id_string=None, uuid=None):
    if uuid:
        return redirect_to_public_link(request, uuid)

    xform, is_owner, can_edit, can_view, can_delete_data = get_xform_and_perms(
        username, id_string, request)
    # no access
    if not (xform.shared or can_view or request.session.get('public_link')):
        return HttpResponseRedirect(reverse(home))

    data = {}
    data['cloned'] = len(
        XForm.objects.filter(user__username__iexact=request.user.username,
                             id_string__exact=id_string + XForm.CLONED_SUFFIX)
    ) > 0
    data['public_link'] = MetaData.public_link(xform)
    data['is_owner'] = is_owner
    data['can_edit'] = can_edit
    data['can_view'] = can_view or request.session.get('public_link')
    data['can_delete_data'] = can_delete_data
    data['xform'] = xform
    data['content_user'] = xform.user
    data['base_url'] = "https://%s" % request.get_host()
    data['media_upload'] = MetaData.media_upload(xform)

    if is_owner:
        data['media_form'] = MediaForm()

    return render(request, "show.html", data)


# SETTINGS SCREEN FOR KPI, LOADED IN IFRAME 
@require_GET
def show_form_settings(request, username=None, id_string=None, uuid=None):
    if uuid:
        return redirect_to_public_link(request, uuid)

    xform, is_owner, can_edit, can_view, can_delete_data = get_xform_and_perms(
        username, id_string, request)
    # no access
    if not (xform.shared or can_view or request.session.get('public_link')):
        return HttpResponseRedirect(reverse(home))

    data = {}
    data['cloned'] = len(
        XForm.objects.filter(user__username__iexact=request.user.username,
                             id_string__exact=id_string + XForm.CLONED_SUFFIX)
    ) > 0
    data['public_link'] = MetaData.public_link(xform)
    data['is_owner'] = is_owner
    data['can_edit'] = can_edit
    data['can_view'] = can_view or request.session.get('public_link')
    data['can_delete_data'] = can_delete_data
    data['xform'] = xform
    data['content_user'] = xform.user
    data['base_url'] = "https://%s" % request.get_host()
    data['source'] = MetaData.source(xform)
    data['media_upload'] = MetaData.media_upload(xform)
    # https://html.spec.whatwg.org/multipage/input.html#attr-input-accept
    # e.g. .csv,.xml,text/csv,text/xml
    media_upload_types = []
    for supported_type in settings.SUPPORTED_MEDIA_UPLOAD_TYPES:
        extension = '.{}'.format(supported_type.split('/')[-1])
        media_upload_types.append(extension)
        media_upload_types.append(supported_type)
    data['media_upload_types'] = ','.join(media_upload_types)

    if is_owner:
        data['media_form'] = MediaForm()

    return render(request, "show_form_settings.html", data)


@require_http_methods(["GET", "OPTIONS"])
def api(request, username=None, id_string=None):
    """
    Returns all results as JSON.  If a parameter string is passed,
    it takes the 'query' parameter, converts this string to a dictionary, an
    that is then used as a MongoDB query string.

    NOTE: only a specific set of operators are allow, currently $or and $and.
    Please send a request if you'd like another operator to be enabled.

    NOTE: Your query must be valid JSON, double check it here,
    http://json.parser.online.fr/

    E.g. api?query='{"last_name": "Smith"}'
    """
    if request.method == "OPTIONS":
        response = HttpResponse()
        add_cors_headers(response)

        return response
    helper_auth_helper(request)
    helper_auth_helper(request)
    xform, owner = check_and_set_user_and_form(username, id_string, request)

    if not xform:
        return HttpResponseForbidden(_('Not shared.'))

    try:
        args = {
            'username': username,
            'id_string': id_string,
            'query': request.GET.get('query'),
            'fields': request.GET.get('fields'),
            'sort': request.GET.get('sort')
        }
        if 'start' in request.GET:
            args["start"] = int(request.GET.get('start'))
        if 'limit' in request.GET:
            args["limit"] = int(request.GET.get('limit'))
        if 'count' in request.GET:
            args["count"] = True if int(request.GET.get('count')) > 0\
                else False
        cursor = ParsedInstance.query_mongo(**args)
    except ValueError as e:
        return HttpResponseBadRequest(e.__str__())

    records = list(record for record in cursor)
    response_text = json_util.dumps(records)

    if 'callback' in request.GET and request.GET.get('callback') != '':
        callback = request.GET.get('callback')
        response_text = ("%s(%s)" % (callback, response_text))

    response = HttpResponse(response_text, content_type='application/json')
    add_cors_headers(response)

    return response


@login_required
@require_GET
def api_token(request, username=None):
    if request.user.username == username:
        user = get_object_or_404(User, username=username)
        data = {}
        data['token_key'], created = Token.objects.get_or_create(user=user)

        return render(request, "api_token.html", data)

    return HttpResponseForbidden(_('Permission denied.'))


@login_required
def edit(request, username, id_string):
    xform = XForm.objects.get(user__username__iexact=username,
                              id_string__exact=id_string)
    owner = xform.user

    if username == request.user.username or\
            request.user.has_perm('logger.change_xform', xform):

        if request.POST.get('media_url'):
            uri = request.POST.get('media_url')
            try:
                SSRFProtect.validate(uri)
            except SSRFProtectException:
                return HttpResponseForbidden(_('URL {uri} is forbidden.').format(
                    uri=uri))
            MetaData.media_add_uri(xform, uri)
        elif request.FILES.get('media'):
            audit = {
                'xform': xform.id_string
            }
            audit_log(
                Actions.FORM_UPDATED, request.user, owner,
                _("Media added to '%(id_string)s'.") %
                {
                    'id_string': xform.id_string
                }, audit, request)
            for aFile in request.FILES.getlist("media"):
                MetaData.media_upload(xform, aFile)

        xform.update()

        if request.is_ajax():
            return HttpResponse(_('Updated succeeded.'))
        else:
            if 'HTTP_REFERER' in request.META and request.META['HTTP_REFERER'].strip(): 
                return HttpResponseRedirect(request.META['HTTP_REFERER'])               

            return HttpResponseRedirect(reverse(show, kwargs={
                'username': username,
                'id_string': id_string
            }))

    return HttpResponseForbidden(_('Update failed.'))


def download_media_data(request, username, id_string, data_id):
    xform = get_object_or_404(
        XForm, user__username__iexact=username,
        id_string__exact=id_string)
    owner = xform.user
    data = get_object_or_404(MetaData, id=data_id)
    dfs = get_storage_class()()
    if request.GET.get('del', False):
        if username == request.user.username:
            try:
                # ensure filename is not an empty string
                if data.data_file.name != '':
                    dfs.delete(data.data_file.name)

                data.delete()
                audit = {
                    'xform': xform.id_string
                }
                audit_log(
                    Actions.FORM_UPDATED, request.user, owner,
                    _("Media download '%(filename)s' deleted from "
                        "'%(id_string)s'.") %
                    {
                        'id_string': xform.id_string,
                        'filename': os.path.basename(data.data_file.name)
                    }, audit, request)
                if 'HTTP_REFERER' in request.META and request.META['HTTP_REFERER'].strip(): 
                    return HttpResponseRedirect(request.META['HTTP_REFERER'])               

                return HttpResponseRedirect(reverse(show, kwargs={
                    'username': username,
                    'id_string': id_string
                }))
            except Exception as e:
                return HttpResponseServerError(e)
    else:
        if username:  # == request.user.username or xform.shared:
            if data.data_file.name == '' and data.data_value is not None:
                return HttpResponseRedirect(data.data_value)

            file_path = data.data_file.name
            filename, extension = os.path.splitext(file_path.split('/')[-1])
            extension = extension.strip('.')
            if dfs.exists(file_path):
                audit = {
                    'xform': xform.id_string
                }
                audit_log(
                    Actions.FORM_UPDATED, request.user, owner,
                    _("Media '%(filename)s' downloaded from "
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

    return HttpResponseForbidden(_('Permission denied.'))


def form_photos(request, username, id_string):
    GALLERY_IMAGE_COUNT_LIMIT = 2500
    GALLERY_THUMBNAIL_CHUNK_SIZE = 25
    GALLERY_THUMBNAIL_CHUNK_DELAY = 5000 # ms

    xform, owner = check_and_set_user_and_form(username, id_string, request)

    if not xform:
        return HttpResponseForbidden(_('Not shared.'))

    data = {}
    data['form_view'] = True
    data['content_user'] = owner
    data['xform'] = xform
    image_urls = []
    too_many_images = False

    # Show the most recent images first
    for instance in xform.instances.all().order_by('-pk'):
        attachments = instance.attachments.all()
        # If we have to truncate, don't include a partial instance
        if len(image_urls) + attachments.count() > GALLERY_IMAGE_COUNT_LIMIT:
            too_many_images = True
            break
        for attachment in attachments:
            # skip if not image e.g video or file
            if not attachment.mimetype.startswith('image'):
                continue

            data = {}
            data['original'] = attachment.secure_url()
            for suffix in settings.THUMB_CONF.keys():
                data[suffix] = attachment.secure_url(suffix)

            image_urls.append(data)

    data['images'] = image_urls
    data['too_many_images'] = too_many_images
    data['thumbnail_chunk_size'] = GALLERY_THUMBNAIL_CHUNK_SIZE
    data['thumbnail_chunk_delay'] = GALLERY_THUMBNAIL_CHUNK_DELAY
    data['profilei'], created = UserProfile.objects.get_or_create(user=owner)

    return render(request, 'form_photos.html', data)
