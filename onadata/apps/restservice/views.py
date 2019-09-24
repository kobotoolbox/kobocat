import json

from django.contrib.auth.decorators import login_required
from django.db.utils import IntegrityError
from django.http import HttpResponse, HttpResponseGone
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.template.base import Template
from django.template.context import Context
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _

from onadata.apps.logger.models.xform import XForm
from onadata.apps.restservice.models import RestService


@login_required
def add_service(request, username, id_string):
    data = {}
    xform = get_object_or_404(
        XForm, user__username__iexact=username, id_string__exact=id_string)
    if request.method == 'POST':
        return HttpResponseGone(
            'New REST services may no longer be added to KoBoCAT. Please '
            'migrate ALL new *and existing* REST services to KPI!'
        )

    # do not show KPI hooks in this legacy view
    data['list_services'] = RestService.objects.filter(
        xform=xform
    ).exclude(name='kpi_hook')
    data['username'] = username
    data['id_string'] = id_string

    return render(request, "add-service.html", data)


def delete_service(request, username, id_string):
    success = "FAILED"
    if request.method == 'POST':
        pk = request.POST.get('service-id')
        if pk:
            try:
                # do not allow KPI hooks to be deleted by this legacy view
                rs = RestService.objects.exclude(name='kpi_hook').get(pk=int(pk))
            except RestService.DoesNotExist:
                pass
            else:
                rs.delete()
                success = "OK"

    return HttpResponse(success)
