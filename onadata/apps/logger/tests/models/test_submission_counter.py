# coding: utf-8
from datetime import datetime

from mock import patch

from onadata.apps.logger.models.submission_counter import SubmissionCounter
from onadata.apps.logger.tasks import create_monthly_counters
from onadata.apps.main.tests.test_base import TestBase


class TestSubmissionCounter(TestBase):

    def setup(self):
        super.setup()

    @patch('onadata.apps.logger.tasks.create_monthly_counters')
    def test_user_created(self, monthly_counter):
        """
        Tests that when a new user is created the celery task runs
        """
        self._create_user('amy', 'amy')
        self._create_user('johnny', 'johnny')

        create_monthly_counters()
        counters = SubmissionCounter.objects.only('user__username')
        self.assertEqual(counters.count(), 4)

    def test_counter_increment(self):
        """
        Tests that when a submission is revieved, the counter increments
        """
        create_monthly_counters()
        self._publish_transportation_form_and_submit_instance()
        counters = SubmissionCounter.objects.get(user__username='bob')
        self.assertEqual(counters.count, 1)

    def test_data_retrieval(self):
        """
        Test that the data stored is the same as the data expected
        """
        create_monthly_counters()
        counter = SubmissionCounter.objects.get(pk=1)
        today = datetime.now()
        print(today.year, today.month)
        self.assertEqual(counter.timestamp.year, today.year)
        self.assertEqual(counter.timestamp.month, today.month)
        self.assertEqual(counter.timestamp.day, 1)
