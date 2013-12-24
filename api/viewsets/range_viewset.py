from django.utils.translation import ugettext as _
from rest_framework import viewsets
from rest_framework import exceptions
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.reverse import reverse

from api.tools import get_accessible_forms, get_min_max_range

from utils.user_auth import check_and_set_form_by_id, \
    check_and_set_form_by_id_string

from odk_logger.models import Instance


class RangeViewSet(viewsets.ViewSet):
    """
Provides the range, max, mean of numeric fields.

* *field* - field to get range, max, mean for

Example:

    GET /api/v1/stats/range/username/1

Response:

    {
        "field_name": {
            "range": 4.5,
            "max": 12.5,
            "min": 8.5
        },
        ...
    }
"""
    permission_classes = [permissions.IsAuthenticated, ]
    lookup_field = 'owner'
    lookup_fields = ('owner', 'formid')
    extra_lookup_fields = None
    queryset = Instance.objects.filter(deleted_at=None)

    def _get_formlist_data_points(self, request, owner=None):
        xforms = get_accessible_forms(owner)
        # filter by tags if available.
        tags = self.request.QUERY_PARAMS.get('tags', None)
        if tags and isinstance(tags, basestring):
            tags = tags.split(',')
            xforms = xforms.filter(tags__name__in=tags).distinct()
        rs = {}
        for xform in xforms.distinct():
            point = {u"%s" % xform.id_string:
                     reverse("range-list", kwargs={
                             "formid": xform.pk,
                             "owner": xform.user.username},
                             request=request)}
            rs.update(point)
        return rs

    def list(self, request, owner=None, formid=None, **kwargs):
        if owner is None and not request.user.is_anonymous():
            owner = request.user.username

        data = []

        if formid:
            try:
                formid = int(formid)
            except ValueError:
                xform = check_and_set_form_by_id_string(formid, request)
            else:
                xform = check_and_set_form_by_id(int(formid), request)
            if not xform:
                raise exceptions.PermissionDenied(
                    _("You do not have permission to "
                      "view data from this form."))
            else:
                try:
                    field = request.QUERY_PARAMS.get('field', None)
                    data = get_min_max_range(xform, field)
                except ValueError as e:
                    raise exceptions.ParseError(detail=e.message)
        else:
            data = self._get_formlist_data_points(request, owner)

        return Response(data)
