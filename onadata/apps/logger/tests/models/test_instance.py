# coding: utf-8
import os
from datetime import timedelta

from dateutil import parser
from django.utils import timezone
from django.test import override_settings
from django_digest.test import DigestAuth
from mock import patch
from reversion import create_revision, is_registered, set_date_created
from reversion.models import Revision

from onadata.apps.main.tests.test_base import TestBase
from onadata.apps.logger.models import XForm, Instance
from onadata.apps.logger.maintenance_tasks import remove_old_revisions
from onadata.apps.logger.models.instance import get_id_string_from_xml_str
from onadata.apps.viewer.models import ParsedInstance
from onadata.libs.utils.common_tags import MONGO_STRFTIME, SUBMISSION_TIME,\
    XFORM_ID_STRING, SUBMITTED_BY


class TestInstance(TestBase):

    def setUp(self):
        super().setUp()

    def create_transportation_fixture_xml_path(self, index = 0):
        return os.path.join(
            self.this_directory,
            "fixtures",
            "transportation",
            "instances",
            self.surveys[index],
            self.surveys[index] + ".xml",
        )

    def test_stores_json(self):
        self._publish_transportation_form_and_submit_instance()
        instances = Instance.objects.all()

        for instance in instances:
            self.assertNotEqual(instance.json, {})

    @patch('django.utils.timezone.now')
    def test_json_assigns_attributes(self, mock_time):
        mock_time.return_value = timezone.datetime.now(timezone.utc)
        self._publish_transportation_form_and_submit_instance()

        xform_id_string = XForm.objects.all()[0].id_string
        instances = Instance.objects.all()

        for instance in instances:
            self.assertEqual(instance.json[SUBMISSION_TIME],
                             mock_time.return_value.strftime(MONGO_STRFTIME))
            self.assertEqual(instance.json[XFORM_ID_STRING],
                             xform_id_string)

    @patch('django.utils.timezone.now')
    def test_json_stores_user_attribute(self, mock_time):
        mock_time.return_value = timezone.datetime.now(timezone.utc)
        self._publish_transportation_form()

        # submit instance with a request user
        path = self.create_transportation_fixture_xml_path()

        auth = DigestAuth(self.login_username, self.login_password)
        self._make_submission(path, auth=auth)

        instances = Instance.objects.filter(xform_id=self.xform).all()
        self.assertTrue(len(instances) > 0)

        for instance in instances:
            self.assertEqual(instance.json[SUBMITTED_BY], 'bob')
            # check that the parsed instance's to_dict_for_mongo also contains
            # the _user key, which is what's used by the JSON REST service
            pi = ParsedInstance.objects.get(instance=instance)
            self.assertEqual(pi.to_dict_for_mongo()[SUBMITTED_BY], 'bob')

    def test_json_time_match_submission_time(self):
        self._publish_transportation_form_and_submit_instance()
        instances = Instance.objects.all()

        for instance in instances:
            # parse with timezone
            date_created = instance.date_created.replace(microsecond=0)
            json_time = parser.parse(f'{instance.json[SUBMISSION_TIME]}+00:00')
            one_second_before = date_created - timedelta(seconds=1)
            one_second_after = date_created + timedelta(seconds=1)
            # GH actions can have 1 (or maybe a few) seconds' difference between
            # instance creation and conversion to json
            self.assertTrue(one_second_before <= json_time <= one_second_after)

    def test_set_instances_with_geopoints_on_submission_false(self):
        self._publish_transportation_form()

        self.assertFalse(self.xform.instances_with_geopoints)

        self._make_submissions()
        xform = XForm.objects.get(pk=self.xform.pk)

        self.assertFalse(xform.instances_with_geopoints)

    def test_set_instances_with_geopoints_on_submission_true(self):
        xls_path = self._fixture_path("gps", "gps.xls")
        self._publish_xls_file_and_set_xform(xls_path)

        self.assertFalse(self.xform.instances_with_geopoints)

        self._make_submissions_gps()
        xform = XForm.objects.get(pk=self.xform.pk)

        self.assertTrue(xform.instances_with_geopoints)

    def test_get_id_string_from_xml_str(self):
        submission = """<?xml version="1.0" encoding="UTF-8" ?>
        <submission xmlns:orx="http://openrosa.org/xforms">
            <data>
                <id_string id="id_string">
                    <element>data</element>
                    <data>random</data>
                </id_string>
            </data>
        </submission>
        """
        id_string = get_id_string_from_xml_str(submission)
        self.assertEqual(id_string, 'id_string')

    def test_reversion(self):
        self.assertTrue(is_registered(Instance))

    @override_settings(KOBOCAT_REVERSION_RETENTION_DAYS=2)
    def test_revision_cleanup(self):
        days_ago_3 = timezone.now() - timedelta(days=3)
        self._publish_transportation_form()

        path = self.create_transportation_fixture_xml_path()

        with create_revision():
            self._make_submission(path, forced_submission_time=days_ago_3)
            set_date_created(days_ago_3)
        old_revision = Revision.objects.first()

        path = self.create_transportation_fixture_xml_path(1)

        with create_revision():
            self._make_submission(path)
        new_revision = Revision.objects.first()

        assert Revision.objects.count() == 2

        remove_old_revisions()

        assert not Revision.objects.filter(id=old_revision.id).exists()
        assert Revision.objects.filter(id=new_revision.id).exists()
