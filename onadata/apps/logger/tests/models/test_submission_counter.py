# coding: utf-8
from datetime import datetime

from django.contrib.auth.models import User

from onadata.apps.logger.models.submission_counter import SubmissionCounter
from onadata.apps.main.tests.test_base import TestBase


class TestSubmissionCounter(TestBase):

    def setup(self):
        super.setup()

    def test_counter_created_on_submission(self):
        """
        Tests that the counter is created when submission is received
        """
        self._create_user_and_login()
        no_counter = SubmissionCounter.objects.filter(user__username='bob')
        self.assertEqual(no_counter.count(), 0)
        self._publish_transportation_form_and_submit_instance()
        counter_added = SubmissionCounter.objects.filter(user__username='bob')
        self.assertEqual(counter_added.count(), 1)

    def test_counter_increment(self):
        """
        Tests that when a submission is revieved, the counter increments
        """
        self._create_user_and_login()
        self._publish_transportation_form_and_submit_instance()
        counters = SubmissionCounter.objects.get(user__username='bob')
        self.assertEqual(counters.count, 1)

    def test_data_retrieval(self):
        """
        Test that the data stored is the same as the data expected
        """
        self._create_user_and_login()
        SubmissionCounter.objects.create(user=User.objects.get(username='bob'))
        counter = SubmissionCounter.objects.last()
        today = datetime.now()
        self.assertEqual(counter.timestamp.year, today.year)
        self.assertEqual(counter.timestamp.month, today.month)
        self.assertEqual(counter.timestamp.day, 1)
