import json

from django.db import transaction
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_POST, require_GET

from onadata.apps.logger.models import XForm, create_xform_copy, copy_xform_data
from onadata.libs.utils.log import audit_log, Actions
from onadata.libs.utils.decorators import is_owner
from onadata.libs.utils.logger_tools import publish_form
from onadata.apps.main.forms import QuickConverter
from onadata.apps.main.views import show
from .factories import data_migrator_factory
from .compare_xml import XFormsComparator


@is_owner
def api_data_migration(request, username, id_string):
    if request.method == 'GET':
        return JsonResponse({
            'info': ('API version of data migration. Required POST request '
                     'sending updated xls form file and migration decisions')
        })
    prepare_migration_data = {
        'username': username,
        'id_string': id_string,
        'is_api_call': True,
    }
    response = update_xform_and_prepare_migration(request, **prepare_migration_data)
    response_data = json.loads(response.content)
    payload = {
        'username': username,
        'old_id_string': response_data['old_id_string'],
        'new_id_string': response_data['new_id_string'],
    }
    return migrate_xform_data(request, **payload)


@is_owner
def pre_migration_view(request, username, id_string):
    return render(request, 'pre_migration_view.html', {
        'username': username,
        'id_string': id_string,
    })


@require_POST
@is_owner
def update_xform_and_prepare_migration(request, username, id_string,
                                       is_api_call=False):
    xform = get_object_or_404(
        XForm, user__username=username, id_string=id_string)
    owner = xform.user
    old_xform = create_xform_copy(xform)

    def set_form():
        form = QuickConverter(request.POST, request.FILES)
        form.publish(request.user, id_string)
        audit = {'xform': xform.id_string}
        audit_log(
            Actions.FORM_XLS_UPDATED, request.user, owner,
            _("XLS for '%(id_string)s' updated.") %
            {
                'id_string': xform.id_string,
            }, audit, request)
        return {
            'type': 'alert-success',
            'text': _(u'Successfully updated %(form_id)s.'
                      u' Please proceed now in data migration') % {
                            'form_id': id_string,
                        }
        }
    message = publish_form(set_form)
    messages.add_message(
        request, messages.INFO, message['text'], extra_tags=message['type'])
    data = {
        'username': username,
        'old_id_string': old_xform.id_string,
        'new_id_string': id_string,
    }
    if is_api_call:
        return JsonResponse(data)

    # XXX: On successful form publish (neither errors nor exceptions occurs),
    # type of message returned by set_form() will be set to alert-success.
    # Following code decision is based on presentation layer, however, this
    # convention is used application-wide, and we do not have to construct try
    # except clauses in order to catch all set_form() errors.
    if message['type'] == 'alert-success':
        return HttpResponseRedirect(reverse('xform-migration-gui',
                                    kwargs=data))
    else:
        return abandon_xform_data_migration(request, **data)


@require_GET
@is_owner
def xform_migration_gui(request, username, old_id_string, new_id_string):
    old_xform = get_object_or_404(
        XForm, user__username=username, id_string=old_id_string)
    new_xform = get_object_or_404(
        XForm, user__username=username, id_string=new_id_string)
    xform_comparator = XFormsComparator(old_xform.xml, new_xform.xml)
    expected_results = xform_comparator.comparison_results()

    return render(request, 'migration_gui.html', {
        'old_id_string': old_xform.id_string,
        'new_id_string': new_xform.id_string,
        'results': expected_results,
        'any_results_present': any(expected_results.values()),
    })


@transaction.atomic
@require_POST
@is_owner
def migrate_xform_data(request, username, old_id_string, new_id_string):
    old_xform = get_object_or_404(
        XForm, user__username=username, id_string=old_id_string)
    new_xform = get_object_or_404(
        XForm, user__username=username, id_string=new_id_string)

    data_migrator = data_migrator_factory(old_xform, new_xform, **request.POST)
    data_migrator.migrate()
    old_xform.delete()  # Delete copy of form's old version

    audit = {'xform': new_id_string}
    audit_log(
        Actions.FORM_DATA_MIGRATED, request.user, new_xform.user,
        _("Data for '%(id_string)s' migrated") %
        {
            'id_string': new_id_string,
        }, audit, request)
    view_data_url = reverse('view-data', kwargs={
        'username': username,
        'id_string': new_id_string,
    })
    message_text = ('Data for %(form_id)s successfuly migrated. '
                    '<a href="%(form_url)s">View data</a>'
                    % {'form_id': new_xform.id_string,
                       'form_url': view_data_url})
    messages.add_message(request, messages.INFO, message_text,
                         extra_tags='alert-success')

    return HttpResponseRedirect(reverse(show, kwargs={
        'username': username,
        'id_string': new_id_string
    }))


@transaction.atomic
@require_POST
@is_owner
def abandon_xform_data_migration(request, username, old_id_string, new_id_string):
    old_xform = get_object_or_404(
        XForm, user__username=username, id_string=old_id_string)
    new_xform = get_object_or_404(
        XForm, user__username=username, id_string=new_id_string)

    # Bring back pre-migration form version and delete copy
    copy_xform_data(from_xform=old_xform, to_xform=new_xform)
    old_xform.delete()

    view_data_url = reverse('view-data', kwargs={
        'username': username,
        'id_string': new_id_string,
    })
    message_text = ('Data migration for %(form_id)s abandoned. '
                    '<a href="%(form_url)s">View data</a>'
                    % {'form_id': new_xform.id_string,
                       'form_url': view_data_url})
    messages.add_message(request, messages.INFO, message_text,
                         extra_tags='alert-info')

    return HttpResponseRedirect(reverse(show, kwargs={
        'username': username,
        'id_string': new_id_string
    }))
