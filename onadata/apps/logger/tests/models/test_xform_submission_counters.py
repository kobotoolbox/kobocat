# coding: utf-8
from datetime import datetime, timedelta

from mock import patch

from onadata.apps.logger.models.xform_daily_submission_counter import DailyXFormSubmissionCounter
from onadata.apps.logger.models.xform_monthly_submission_counter import MonthlyXFormSubmissionCounter
from onadata.apps.logger.tasks import delete_daily_counters
from onadata.apps.main.tests.test_base import TestBase


class TestXFormSubmissionCounters(TestBase):

    def setup(self):
        super.setup()

    def test_xform_counter_increments(self):
        """
        Test xform counters increase when an instance is saved
        """
        self._publish_transportation_form_and_submit_instance()
        daily_counters = DailyXFormSubmissionCounter.objects.get(
            xform__user__username='bob'
        )
        self.assertEqual(daily_counters.counter, 1)
        monthly_counters = MonthlyXFormSubmissionCounter.objects.get(
            user__username='bob'
        )
        self.assertEqual(monthly_counters.counter, 1)

    def test_data_retrieval(self):
        """
        Test that the data stored is the same as the data expected
        """
        self._publish_transportation_form_and_submit_instance()

        daily_counter = DailyXFormSubmissionCounter.objects.last()
        today = datetime.now()
        self.assertEqual(daily_counter.date.year, today.year)
        self.assertEqual(daily_counter.date.month, today.month)
        self.assertEqual(daily_counter.date.day, today.day)

        monthly_counter = MonthlyXFormSubmissionCounter.objects.last()
        today = datetime.now()
        self.assertEqual(monthly_counter.month, today.month)
        self.assertEqual(monthly_counter.year, today.year)

    @patch('onadata.apps.logger.tasks.delete_daily_counters')
    def test_delete_daily_counters(self, daily_counts):
        """
        Test that the delete_daily_counters task deleted counters that are
        more than 31 days old
        """
        self._publish_transportation_form_and_submit_instance()
        counter = DailyXFormSubmissionCounter.objects.last()
        counter.date = counter.date - timedelta(days=32)
        counter.save()
        delete_daily_counters()
        daily_counters = DailyXFormSubmissionCounter.objects.all()
        self.assertEqual(daily_counters.count(), 0)
