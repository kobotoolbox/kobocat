# coding: utf-8
from __future__ import unicode_literals, print_function, division, absolute_import

import os
import re
from tempfile import NamedTemporaryFile

from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import (
    AnonymousUser,
    Permission,
    User
)
from django.test import TestCase
from django_digest.test import Client as DigestClient
from django_digest.test import DigestAuth
from rest_framework.reverse import reverse
from rest_framework.test import APIRequestFactory

from onadata.apps.api.viewsets.metadata_viewset import MetaDataViewSet
from onadata.apps.logger.models import Instance, XForm, Attachment
from onadata.apps.logger.views import submission
from onadata.apps.main import tests as main_tests
from onadata.apps.main.models import UserProfile, MetaData


class TestAbstractViewSet(TestCase):
    surveys = ['transport_2011-07-25_19-05-49',
               'transport_2011-07-25_19-05-36',
               'transport_2011-07-25_19-06-01',
               'transport_2011-07-25_19-06-14']
    main_directory = os.path.dirname(main_tests.__file__)

    profile_data = {
        'username': 'bob',
        'email': 'bob@columbia.edu',
        'password1': 'bobbob',
        'password2': 'bobbob',
        'name': 'Bob',
        'city': 'Bobville',
        'country': 'US',
        'organization': 'Bob Inc.',
        'home_page': 'bob.com',
        'twitter': 'boberama'
    }

    def setUp(self):
        super(TestAbstractViewSet, self).setUp()
        self.factory = APIRequestFactory()
        self._login_user_and_profile()
        self._add_permissions_to_user(AnonymousUser())
        self.maxDiff = None

    def publish_xls_form(self):
        data = {
            'owner': self.user.username,
            'public': False,
            'public_data': False,
            'description': u'transportation_2011_07_25',
            'downloadable': True,
            'allows_sms': False,
            'encrypted': False,
            'sms_id_string': u'transportation_2011_07_25',
            'id_string': u'transportation_2011_07_25',
            'title': u'transportation_2011_07_25',
        }

        path = os.path.join(
            settings.ONADATA_DIR, "apps", "main", "tests", "fixtures",
            "transportation", "transportation.xls")

        xform_list_url = reverse('xform-list')

        with open(path) as xls_file:
            post_data = {'xls_file': xls_file}
            response = self.client.post(xform_list_url, data=post_data)
            self.assertEqual(response.status_code, 201)
            self.xform = XForm.objects.all().order_by('pk').reverse()[0]
            data.update({
                'url':
                    'http://testserver/api/v1/forms/%s' % (self.xform.pk)
            })

            self.assertDictContainsSubset(data, response.data)
            self.form_data = response.data

    def user_profile_data(self):
        return {
            'id': self.user.pk,
            'url': 'http://testserver/api/v1/profiles/bob',
            'username': 'bob',
            'name': 'Bob',
            'email': 'bob@columbia.edu',
            'city': 'Bobville',
            'country': 'US',
            'organization': 'Bob Inc.',
            'website': 'bob.com',
            'twitter': 'boberama',
            'gravatar': self.user.profile.gravatar,
            'require_auth': False,
            'user': 'http://testserver/api/v1/users/bob',
            'metadata': {},
        }

    def _add_permissions_to_user(self, user, save=True):
        """
        Gives `user` unrestricted model-level access to everything listed in
        `auth_permission`.  Without this, actions on individual instances are
        immediately denied and object-level permissions are never considered.
        """
        if user.is_anonymous():
            user = User.objects.get(id=settings.ANONYMOUS_USER_ID)
        user.user_permissions = Permission.objects.all()
        if save:
            user.save()

    def _set_api_permissions(self, user):
        add_userprofile = Permission.objects.get(
            content_type__app_label='main', content_type__model='userprofile',
            codename='add_userprofile')
        user.user_permissions.add(add_userprofile)

    def _create_user_profile(self, extra_post_data={}):
        self.profile_data = dict(
            self.profile_data.items() + extra_post_data.items())
        user, created = User.objects.get_or_create(
            username=self.profile_data['username'],
            first_name=self.profile_data['name'],
            email=self.profile_data['email'])
        user.set_password(self.profile_data['password1'])
        self._add_permissions_to_user(user, save=False)
        user.save()
        new_profile, created = UserProfile.objects.get_or_create(
            user=user, name=self.profile_data['name'],
            city=self.profile_data['city'],
            country=self.profile_data['country'],
            organization=self.profile_data['organization'],
            home_page=self.profile_data['home_page'],
            twitter=self.profile_data['twitter'],
            require_auth=False
        )

        return new_profile

    def _login_user_and_profile(self, extra_post_data={}):
        profile = self._create_user_profile(extra_post_data)
        self.user = profile.user
        self.assertTrue(
            self.client.login(username=self.user.username,
                              password=self.profile_data['password1']))
        self.extra = {
            'HTTP_AUTHORIZATION': 'Token %s' % self.user.auth_token}

    def _add_uuid_to_submission_xml(self, path, xform):
        tmp_file = NamedTemporaryFile(delete=False)
        split_xml = None

        with open(path) as _file:
            split_xml = re.split(r'(<transport>)', _file.read())

        split_xml[1:1] = [
            '<formhub><uuid>%s</uuid></formhub>' % xform.uuid
        ]
        tmp_file.write(''.join(split_xml))
        path = tmp_file.name
        tmp_file.close()

        return path

    def _make_submission(self, path, username=None, add_uuid=False,
                         forced_submission_time=None,
                         client=None, media_file=None, auth=None):
        # store temporary file with dynamic uuid
        self.factory = APIRequestFactory()
        if auth is None:
            auth = DigestAuth(self.profile_data['username'],
                              self.profile_data['password1'])

        tmp_file = None

        if add_uuid:
            path = self._add_uuid_to_submission_xml(path, self.xform)
        with open(path) as f:
            post_data = {'xml_submission_file': f}

            if media_file is not None:
                post_data['media_file'] = media_file

            if username is None:
                username = self.user.username

            url_prefix = '%s/' % username if username else ''
            url = '/%ssubmission' % url_prefix

            request = self.factory.post(url, post_data)
            request.user = authenticate(username=auth.username,
                                        password=auth.password)
            self.response = submission(request, username=username)

            if auth and self.response.status_code == 401:
                request.META.update(auth(request.META, self.response))
                self.response = submission(request, username=username)

        if forced_submission_time:
            instance = Instance.objects.order_by('-pk').all()[0]
            instance.date_created = forced_submission_time
            instance.save()
            instance.parsed_instance.save()

        # remove temporary file if stored
        if add_uuid:
            os.unlink(tmp_file.name)

    def _make_submissions(self, username=None, add_uuid=False,
                          should_store=True):
        """Make test fixture submissions to current xform.

        :param username: submit under this username, default None.
        :param add_uuid: add UUID to submission, default False.
        :param should_store: should submissions be save, default True.
        """
        paths = [os.path.join(
            self.main_directory, 'fixtures', 'transportation',
            'instances', s, s + '.xml') for s in self.surveys]
        pre_count = Instance.objects.count()

        auth = DigestAuth(self.profile_data['username'],
                          self.profile_data['password1'])
        for path in paths:
            self._make_submission(path, username, add_uuid, auth=auth)
        post_count = pre_count + len(self.surveys) if should_store\
            else pre_count
        self.assertEqual(Instance.objects.count(), post_count)
        self.assertEqual(self.xform.instances.count(), post_count)
        xform = XForm.objects.get(pk=self.xform.pk)
        self.assertEqual(xform.num_of_submissions, post_count)
        self.assertEqual(xform.user.profile.num_of_submissions, post_count)

    def _submit_transport_instance_w_attachment(self,
                                                survey_at=0,
                                                media_file=None):
        s = self.surveys[survey_at]
        if not media_file:
            media_file = "1335783522563.jpg"
        path = os.path.join(self.main_directory, 'fixtures',
                            'transportation', 'instances', s, media_file)
        with open(path) as f:
            self._make_submission(os.path.join(
                self.main_directory, 'fixtures',
                'transportation', 'instances', s, s + '.xml'), media_file=f)

        attachment = Attachment.objects.all().reverse()[0]
        self.attachment = attachment

    def _post_form_metadata(self, data, test=True):
        count = MetaData.objects.count()
        view = MetaDataViewSet.as_view({'post': 'create'})
        request = self.factory.post('/', data, **self.extra)

        response = view(request)

        if test:
            self.assertEqual(response.status_code, 201)
            another_count = MetaData.objects.count()
            self.assertEqual(another_count, count + 1)
            self.metadata = MetaData.objects.get(pk=response.data['id'])
            self.metadata_data = response.data

        return response

    def _add_form_metadata(self, xform, data_type, data_value, path=None):
        data = {
            'data_type': data_type,
            'data_value': data_value,
            'xform': xform.pk
        }

        if path and data_value:
            with open(path) as media_file:
                data.update({
                    'data_file': media_file,
                })
                self._post_form_metadata(data)
        else:
            self._post_form_metadata(data)

    def _get_digest_client(self):
        self.user.profile.require_auth = True
        self.user.profile.save()
        client = DigestClient()
        client.set_authorization(self.profile_data['username'],
                                 self.profile_data['password1'],
                                 'Digest')
        return client
