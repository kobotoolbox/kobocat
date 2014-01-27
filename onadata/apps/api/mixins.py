from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import get_object_or_404

from guardian.shortcuts import get_objects_for_user

from rest_framework import serializers, mixins
from rest_framework.exceptions import ParseError


class ObjectLookupMixin(object):
    def get_object(self, queryset=None):
        """
        Incase the lookup is on an object that has been hyperlinked
        then update the queryset filter appropriately
        """
        if self.kwargs.get(self.lookup_field, None) is None:
            raise ParseError(
                'Expected URL keyword argument `%s`.' % self.lookup_field
            )
        if queryset is None:
            queryset = self.filter_queryset(self.get_queryset())
        filter = {}
        serializer = self.get_serializer()
        lookup_field = self.lookup_field
        if self.lookup_field in serializer.get_fields():
            k = serializer.get_fields()[self.lookup_field]
            if isinstance(k, serializers.HyperlinkedRelatedField):
                lookup_field = '%s__%s' % (self.lookup_field, k.lookup_field)
        filter[lookup_field] = self.kwargs[self.lookup_field]
        return get_object_or_404(queryset,  **filter)

    def pre_save(self, obj):
        """
        Set any attributes on the object that are implicit in the request.
        """
        # pk and/or slug attributes are implicit in the URL.
        lookup = self.kwargs.get(self.lookup_field, None)
        pk = self.kwargs.get(self.pk_url_kwarg, None)
        slug = self.kwargs.get(self.slug_url_kwarg, None)
        slug_field = slug and self.slug_field or None

        if lookup:
            serializer = self.get_serializer()
            k = serializer.get_fields()[self.lookup_field]
            queryset = self.get_queryset()
            queryset = self.filter_queryset(queryset)
            if isinstance(k, serializers.HyperlinkedRelatedField):
                filter = {}
                lookup_field = '%s__%s' % (self.lookup_field, k.lookup_field)
                filter[lookup_field] = lookup
                k_obj = get_object_or_404(queryset, **filter)
                lookup = getattr(k_obj, self.lookup_field)
            setattr(obj, self.lookup_field, lookup)

        if pk:
            setattr(obj, 'pk', pk)

        if slug:
            setattr(obj, slug_field, slug)

        # Ensure we clean the attributes so that we don't eg return integer
        # pk using a string representation, as provided by the url conf kwarg.
        if hasattr(obj, 'full_clean'):
            exclude = mixins._get_validation_exclusions(
                obj, pk, slug_field, self.lookup_field)
            obj.full_clean(exclude)


class MultiLookupMixin(object):
    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.filter_queryset(self.get_queryset())
        filter = {}
        serializer = self.get_serializer()
        lookup_fields = getattr(self, 'lookup_fields', [])
        for field in lookup_fields:
            lookup_field = field
            if lookup_field in serializer.get_fields():
                k = serializer.get_fields()[lookup_field]
                if isinstance(k, serializers.HyperlinkedRelatedField):
                    if k.source:
                        lookup_field = k.source
                    lookup_field = '%s__%s' % (lookup_field, k.lookup_field)
            if self.kwargs.get(field, None) is None:
                raise ParseError(
                    'Expected URL keyword argument `%s`.' % field
                )
            filter[lookup_field] = self.kwargs[field]
        # lookup_field = self.lookup_field
        return get_object_or_404(queryset,  **filter)


class ViewPermissionMixin(object):

    def get_queryset(self):
        """
        Get the list of items for this view
        based on user's view_%(model_name)s permissions.
        """
        self.model = self.model if self.model is not None else \
            self.queryset.model if self.queryset is not None else None
        if self.request is not None and self.model is not None:
            kwargs = {
                'app_label': self.model._meta.app_label,
                'model_name': self.model._meta.module_name
            }
            perms = ['%(app_label)s.view_%(model_name)s' % kwargs]
            return get_objects_for_user(self.request.user, perms, self.model)

        if self.model is not None:
            return self.model._default_manager.all()

        raise ImproperlyConfigured("'%s' must define 'queryset' or 'model'"
                                   % self.__class__.__name__)
