import json

from django.db import transaction
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_POST, require_GET

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view

from onadata.apps.logger.models import XForm, create_xform_copy, copy_xform_data
from onadata.libs.utils.log import audit_log, Actions
from onadata.libs.utils.decorators import is_owner
from onadata.libs.utils.logger_tools import publish_form
from onadata.apps.main.forms import QuickConverter
from onadata.apps.main.views import show
from .restore_backup import BackupRestorer, BackupRestoreError
from .factories import data_migrator_factory
from .compare_xml import XFormsComparator


class DataMigrationEndpoint(APIView):
    def get(self, request):
        return Response({
            'info': ('API version of data migration. Required POST request '
                     'sending updated xls form file and migration decisions')
        })

    def post(self, request, username, id_string):
        update_xform_data = {
            'request': request,
            'username': username,
            'id_string': id_string,
            'add_message': False,
        }
        update_xform_results = _update_xform(**update_xform_data)
        success = update_xform_results.pop('success')
        if success:
            decisions = json.loads(request.POST['json'])
            update_xform_results['migration_decisions'] = decisions
            _migrate_xform(**update_xform_results)
            return Response({'info': 'Form updated successfully'})
        else:
            _abandon_migration_handler(**update_xform_results)
            return Response({'info': 'Could not update xform'}, status=500)


@is_owner
def pre_migration_view(request, username, id_string):
    return render(request, 'pre_migration_view.html', {
        'username': username,
        'id_string': id_string,
    })


def _update_xform(request, username, id_string, add_message=True):
    xform = get_object_or_404(
        XForm, user__username=username, id_string=id_string)
    owner = xform.user
    old_xform = create_xform_copy(xform)

    def _rename_migrated_files(files):
        # XXX: later stages of form processing assume that filename
        # is form's id_string
        file = files.get('xls_file')
        if file is not None:
            id_string_name = '{}.xlsx'.format(id_string)
            file._set_name(id_string_name)

    def set_form():
        _rename_migrated_files(request.FILES)
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

    if add_message:
        messages.add_message(request, messages.INFO, message['text'],
                             extra_tags=message['type'])

    # XXX: On successful form publish (neither errors nor exceptions occurs),
    # type of message returned by set_form() will be set to alert-success.
    # Following code decision is based on presentation layer, however, this
    # convention is used application-wide, and we do not have to construct try
    # except clauses in order to catch all set_form() errors.
    return {
        'success': message['type'] == 'alert-success',
        'username': username,
        'old_id_string': old_xform.id_string,
        'new_id_string': id_string,
    }


@require_POST
@is_owner
def update_xform_and_prepare_migration(request, username, id_string):
    xform_results = _update_xform(request, username, id_string)
    success = xform_results.pop('success')
    if success:
        return HttpResponseRedirect(reverse('xform-migration-gui',
                                            kwargs=xform_results))
    else:
        return abandon_xform_data_migration(request, **xform_results)


@require_GET
@is_owner
def xform_migration_gui(request, username, old_id_string, new_id_string):
    old_xform = get_object_or_404(
        XForm, user__username=username, id_string=old_id_string)
    new_xform = get_object_or_404(
        XForm, user__username=username, id_string=new_id_string)
    xform_comparator = XFormsComparator(old_xform.xml, new_xform.xml)
    comparison_results = xform_comparator.comparison_results()

    return render(request, 'migration_gui.html', {
        'old_id_string': old_xform.id_string,
        'new_id_string': new_xform.id_string,
        'results': comparison_results,
        'any_results_present': any(comparison_results.values()),
    })


def _migrate_xform(username, old_id_string, new_id_string, migration_decisions):
    old_xform = get_object_or_404(
        XForm, user__username=username, id_string=old_id_string)
    new_xform = get_object_or_404(
        XForm, user__username=username, id_string=new_id_string)

    data_migrator = data_migrator_factory(old_xform, new_xform,
                                          **migration_decisions)
    data_migrator.migrate()
    old_xform.delete()  # Delete copy of form's old version

    return new_xform


@transaction.atomic
@require_POST
@is_owner
def migrate_xform_data(request, username, old_id_string, new_id_string):
    new_xform = _migrate_xform(username, old_id_string, new_id_string, request.POST)

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


def _abandon_migration_handler(username, old_id_string, new_id_string):
    old_xform = get_object_or_404(
        XForm, user__username=username, id_string=old_id_string)
    new_xform = get_object_or_404(
        XForm, user__username=username, id_string=new_id_string)

    # Bring back pre-migration form version and delete copy
    copy_xform_data(from_xform=old_xform, to_xform=new_xform)
    old_xform.delete()
    return new_xform


@transaction.atomic
@require_POST
@is_owner
def abandon_xform_data_migration(request, username, old_id_string, new_id_string):
    new_xform = _abandon_migration_handler(username, old_id_string, new_id_string)

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


@is_owner
def compare_xforms(request, username, id_string):
    existing_xform = get_object_or_404(
        XForm, user__username=username, id_string=id_string)

    comparable_xform = QuickConverter(request.POST, request.FILES)
    xform_comparator = XFormsComparator(existing_xform.xml, comparable_xform.xml)
    comparison_results = xform_comparator.comparison_results()
    return Response(comparison_results)


@is_owner
def pre_restore_backup(request, username, id_string):
    return render(request, 'pre_restore_backup.html', {
        'username': username,
        'id_string': id_string,
    })


def handle_restoring_backup(request, username, id_string):
    response = restore_backup(request, username, id_string)

    if response.status_code == 200:
        msg_text = 'Backup successfully restored'
        msg_tags = 'alert-success'
    else:
        msg_text = 'Could not restore backup. Please contact us for more details'
        msg_tags = 'alert-error'

    messages.add_message(request, messages.INFO, msg_text, extra_tags=msg_tags)

    return HttpResponseRedirect(reverse(show, kwargs={
        'username': username,
        'id_string': id_string
    }))


@api_view(['POST'])
def restore_backup(request, username, id_string):
    version = request.POST.get('version')
    restore_last = request.POST.get('restore_last')
    xform = get_object_or_404(XForm, user__username=username,
                              id_string=id_string)
    try:
        BackupRestorer(xform, version, restore_last).restore_xform_backup()
    except BackupRestoreError as e:
        return Response({'info': str(e)}, status=400)

    return Response({'info': 'Backup restored successfully'})
