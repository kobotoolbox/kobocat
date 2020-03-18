# coding: utf-8
from __future__ import unicode_literals, absolute_import

from django.contrib.contenttypes.models import ContentType
from guardian.models import UserObjectPermission
from guardian.shortcuts import assign_perm
from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from onadata.apps.api import permissions
from onadata.libs.permissions import CAN_VIEW_XFORM
from onadata.libs.mixins.view_permission_mixin import ViewPermissionMixin
from onadata.libs.serializers.note_serializer import NoteSerializer
from onadata.apps.logger.models import Note, XForm


class NoteViewSet(ViewPermissionMixin, ModelViewSet):
    """## Add Notes to a submission

A `POST` payload of parameters:

    `note` - the note string to add to a data point
    `instance` - the data point id

 <pre class="prettyprint">
  <b>POST</b> /api/v1/notes</pre>

Payload

    {"instance": 1, "note": "This is a note."}

  > Response
  >
  >     {
  >          "id": 1,
  >          "instance": 1,
  >          "note": "This is a note."
  >          ...
  >     }
  >
  >     HTTP 201 OK

# Get List of notes for a data point

A `GET` request will return the list of notes applied to a data point.

 <pre class="prettyprint">
  <b>GET</b> /api/v1/notes</pre>


  > Response
  >
  >     [{
  >          "id": 1,
  >          "instance": 1,
  >          "note": "This is a note."
  >          ...
  >     }, ...]
  >
  >
  >        HTTP 200 OK
"""
    queryset = Note.objects.all()
    serializer_class = NoteSerializer
    permission_classes = [
        permissions.ViewDjangoObjectPermissions,
        permissions.IsAuthenticated
    ]

    def get_queryset(self):
        # Allows users to see only notes of instances they're allowed to see
        user = self.request.user
        xform_content_type = ContentType.objects.get(app_label='logger',
                                                     model='xform')
        user_xform_ids = [
            int(id_) for id_ in UserObjectPermission.objects.filter(
                content_type=xform_content_type,
                permission__codename=CAN_VIEW_XFORM,
                user_id__in=user.pk).values_list('object_pk',
                                                 flat=True).distinct()
        ]

        anonymous_xform_ids = [
            int(id_) for id_ in XForm.objects.filter(shared_data=True)
            .values_list('pk', flat=True).distinct()
        ]

        xform_ids = set(anonymous_xform_ids + user_xform_ids)

        return Note.objects.filter(instance__xform_id__in=xform_ids).all()

    # This used to be post_save. Part of it is here, permissions validation
    # has been moved to the note serializer
    def perform_create(self, serializer):
        obj = serializer.save(user=self.request.user)
        assign_perm('add_note', self.request.user, obj)
        assign_perm('change_note', self.request.user, obj)
        assign_perm('delete_note', self.request.user, obj)
        assign_perm('view_note', self.request.user, obj)
        # make sure parsed_instance saves to mongo db
        obj.instance.parsed_instance.save()

    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        instance = obj.instance
        obj.delete()
        # update mongo data
        instance.parsed_instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
