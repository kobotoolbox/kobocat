# coding: utf-8
from __future__ import unicode_literals, print_function, division, absolute_import

from django.shortcuts import get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from django.utils import six
from rest_framework import filters
from rest_framework.exceptions import ParseError

from onadata.apps.logger.models import XForm, Instance


class AnonDjangoObjectPermissionFilter(filters.DjangoObjectPermissionsFilter):
    def filter_queryset(self, request, queryset, view):
        """
        Anonymous user has no object permissions, return queryset as it is.
        """
        if request.user.is_anonymous():
            return queryset

        return super(AnonDjangoObjectPermissionFilter, self)\
            .filter_queryset(request, queryset, view)


class XFormListObjectPermissionFilter(AnonDjangoObjectPermissionFilter):
    perm_format = '%(app_label)s.report_%(model_name)s'


class XFormOwnerFilter(filters.BaseFilterBackend):

    owner_prefix = 'user'

    def filter_queryset(self, request, queryset, view):
        owner = request.query_params.get('owner')

        if owner:
            kwargs = {
                self.owner_prefix + '__username': owner
            }

            return queryset.filter(**kwargs)

        return queryset


class XFormIdStringFilter(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        id_string = request.query_params.get('id_string')
        if id_string:
            return queryset.filter(id_string=id_string)
        return queryset


class TagFilter(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        # filter by tags if available.
        tags = request.query_params.get('tags', None)

        if tags and isinstance(tags, six.string_types):
            tags = tags.split(',')
            return queryset.filter(tags__name__in=tags)

        return queryset


class XFormPermissionFilterMixin(object):

    @staticmethod
    def _get_xform(request, queryset, view, keyword):
        xform_id = request.query_params.get('xform')
        if not xform_id:
            lookup_field = view.lookup_field
            lookup = view.kwargs.get(lookup_field)
            if not lookup:
                return
            try:
                xform_id = queryset.values_list(
                    '{keyword}_id'.format(keyword=keyword), flat=True
                ).get(pk=lookup)
            except ObjectDoesNotExist:
                raise Http404

        try:
            int(xform_id)
        except ValueError:
            raise ParseError(
                'Invalid value for formid {form_id}.'.format(form_id=xform_id)
            )

        return get_object_or_404(XForm, pk=xform_id)

    def _xform_filter_queryset(self, request, queryset, view, keyword):
        """Use XForm permissions"""

        xform_qs = XForm.objects.all()
        xform = self._get_xform(request, queryset, view, keyword)

        # Anonymous user should not be able to list any data from publicly
        # shared xforms except if they know the direct link.
        # if `xform` is provided,
        # e.g.: `/api/v1/metadata.json?xform=1` for XForm #1
        # or they access a metadata object directly
        # e.g.: `/api/v1/metadata/5.json` for MetaData #5
        # we include all publicly shared xforms
        if xform:
            if xform.shared:
                kwargs = {keyword: xform.pk}
                return queryset.filter(**kwargs)

            xform_qs = xform_qs.filter(pk=xform.pk)

        xforms = super(XFormPermissionFilterMixin, self).filter_queryset(
            request, xform_qs, view
        )

        kwargs = {'{keyword}__in'.format(keyword=keyword): xforms}
        return queryset.filter(**kwargs)


class MetaDataFilter(XFormPermissionFilterMixin,
                     filters.DjangoObjectPermissionsFilter):
    def filter_queryset(self, request, queryset, view):
        queryset = self._xform_filter_queryset(request, queryset, view, 'xform')
        data_type = request.query_params.get('data_type')
        if data_type is not None:
            queryset = queryset.filter(data_type=data_type)
        return queryset


class AttachmentFilter(XFormPermissionFilterMixin,
                       filters.DjangoObjectPermissionsFilter):
    def filter_queryset(self, request, queryset, view):
        queryset = self._xform_filter_queryset(request, queryset, view,
                                               'instance__xform')
        instance_id = request.query_params.get('instance')
        if instance_id:
            try:
                int(instance_id)
            except ValueError:
                raise ParseError(
                    "Invalid value for instance %s." % instance_id)
            instance = get_object_or_404(Instance, pk=instance_id)
            queryset = queryset.filter(instance=instance)

        return queryset
