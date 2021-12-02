# coding: utf-8
import os
import re
from tempfile import NamedTemporaryFile

from django.contrib.auth import authenticate
from django_digest.test import DigestAuth
from rest_framework.test import APIRequestFactory

from onadata.apps.api.viewsets.xform_submission_api import XFormSubmissionApi
from onadata.apps.logger.models import Instance, XForm


class MakeSubmissionMixin:

    @property
    def submission_view(self):
        if not hasattr(self, '_submission_view'):
            setattr(self, '_submission_view', XFormSubmissionApi.as_view({
                "head": "create",
                "post": "create"
            }))
        return self._submission_view

    def _add_uuid_to_submission_xml(self, path, xform):
        with open(path, 'rb') as _file:
            split_xml = re.split(r'(<transport>)', _file.read().decode())

        split_xml[1:1] = [f'<formhub><uuid>{xform.uuid}</uuid></formhub>']

        with NamedTemporaryFile(delete=False, mode='w') as tmp_file:
            tmp_file.write(''.join(split_xml))
            path = tmp_file.name

        return path

    def _make_submission(
        self,
        path,
        username=None,
        add_uuid=False,
        forced_submission_time=None,
        auth=None,
        client=None,
        media_file=None,
    ):
        # store temporary file with dynamic uuid

        self.factory = APIRequestFactory()
        if auth is None:
            auth = DigestAuth('bob', 'bob')

        if add_uuid:
            path = self._add_uuid_to_submission_xml(path, self.xform)

        with open(path, 'rb') as f:
            post_data = {'xml_submission_file': f}

            if media_file is not None:
                post_data['media_file'] = media_file

            if username is None:
                username = self.user.username

            url_prefix = f'{username}/' if username else ''
            url = f'/{url_prefix}submission'
            request = self.factory.post(url, post_data)
            request.user = authenticate(username=auth.username,
                                        password=auth.password)
            self.response = None  # Reset in case error in viewset below
            self.response = self.submission_view(request, username=username)
            if auth and self.response.status_code == 401:
                request.META.update(auth(request.META, self.response))
                self.response = self.submission_view(request, username=username)

        if forced_submission_time:
            instance = Instance.objects.order_by('-pk').all()[0]
            instance.date_created = forced_submission_time
            instance.save()
            instance.parsed_instance.save()

        # remove temporary file if stored
        if add_uuid:
            os.unlink(path)

    def _make_submission_w_attachment(self, path, attachment_path):

        with open(path, 'rb') as f:
            a = open(attachment_path, 'rb')
            post_data = {'xml_submission_file': f, 'media_file': a}
            url = f'/{self.user.username}/submission'
            auth = DigestAuth('bob', 'bob')
            self.factory = APIRequestFactory()
            request = self.factory.post(url, post_data)
            request.user = authenticate(
                username='bob', password='bob'
            )
            self.response = self.submission_view(
                request, username=self.user.username
            )

            if auth and self.response.status_code == 401:
                request.META.update(auth(request.META, self.response))
                self.response = self.submission_view(
                    request, username=self.user.username
                )

    def _make_submissions(
        self,
        username=None,
        add_uuid=False,
        should_store=True,
        auth=None,
        module_directory=None,
    ):
        """
        Make test fixture submissions to current xform.

        :param username: submit under this username, default None.
        :param add_uuid: add UUID to submission, default False.
        :param should_store: should submissions be save, default True.
        """

        if not module_directory:
            module_directory = self.this_directory

        paths = [os.path.join(
            module_directory, 'fixtures', 'transportation',
            'instances', s, s + '.xml') for s in self.surveys]
        pre_count = Instance.objects.count()

        for path in paths:
            self._make_submission(path, username, add_uuid, auth=auth)

        post_count = (
            pre_count + len(self.surveys) if should_store else pre_count
        )

        self.assertEqual(Instance.objects.count(), post_count)
        self.assertEqual(self.xform.instances.count(), post_count)
        xform = XForm.objects.get(pk=self.xform.pk)
        self.assertEqual(xform.num_of_submissions, post_count)
        self.assertEqual(xform.user.profile.num_of_submissions, post_count)
