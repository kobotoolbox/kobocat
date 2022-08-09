# coding: utf-8
import math
from collections import defaultdict
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count, Value, F, DateField
from django.db.models.functions import Cast, Concat
from django.utils import timezone

from onadata.apps.logger.models import (
    DailyXFormSubmissionCounter,
    MonthlyXFormSubmissionCounter,
)
from onadata.apps.main.models.user_profile import UserProfile
from onadata.libs.utils.jsonbfield_helper import ReplaceValues


class Command(BaseCommand):

    help = "Updates monthly and daily submission counters"

    def add_arguments(self, parser):
        parser.add_argument(
            '--chunks',
            type=int,
            default=2000,
            help="Number of records to process per query"
        )

        week_default = math.ceil(settings.DAILY_COUNTERS_MAX_DAYS / 4)
        parser.add_argument(
            '--weeks',
            type=int,
            default=week_default,
            help=(
                f"Number of months taken into account to populate the counters. "
                f"Default is {week_default}"
            ),
        )

    def handle(self, *args, **kwargs):
        chunks = kwargs['chunks']
        weeks = kwargs['weeks']
        verbosity = kwargs['verbosity']

        today = timezone.now().date()
        delta = timedelta(weeks=weeks)
        date_threshold = today - delta
        # We want to take the first day of the month to get accurate count for
        # monthly counters
        date_threshold = date_threshold.replace(day=1)
        if verbosity >= 1:
            self.stdout.write(
                f'Daily and monthly counters will be (re)calculated '
                f'since {date_threshold.strftime("%Y-%m-%d UTC")}'
            )

        # Release any locks on the users' profile from getting submissions
        UserProfile.objects.exclude(
            metadata__counters_updates_status='complete'
        ).update(
            metadata=ReplaceValues(
                'metadata',
                updates={'submissions_suspended': False},
            ),
        )

        # Get only xforms whose users' storage counters have not been updated yet.
        up_queryset = UserProfile.objects.values_list('user_id', flat=True).filter(
            metadata__counters_updates_status='complete'
        )

        for user in (
            User.objects.only('username')
            .exclude(pk=settings.ANONYMOUS_USER_ID)
            .exclude(pk__in=up_queryset)
            .iterator(chunk_size=chunks)
        ):
            if verbosity >= 1:
                self.stdout.write(f'Processing user {user.username}...')

            total_submissions = defaultdict(int)
            monthly_counters = []

            # Retrieve or create user's profile.
            (
                user_profile,
                created,
            ) = UserProfile.objects.get_or_create(user_id=user.pk)

            # Some old profiles don't have metadata
            if user_profile.metadata is None:
                user_profile.metadata = {}

            # Set the flag to true if it was never set.
            if not user_profile.metadata.get('submissions_suspended'):
                # We are using the flag `submissions_suspended` to prevent
                # new submissions from coming in while the
                # counters are being calculated.
                user_profile.metadata['submissions_suspended'] = True
                user_profile.save(update_fields=['metadata'])

            with transaction.atomic():

                # First delete only records covered by desired max days.
                if verbosity >= 2:
                    self.stdout.write(f'\tDeleting old data...')
                DailyXFormSubmissionCounter.objects.filter(
                    xform__user_id=user.pk, date__gte=date_threshold
                ).delete()

                # Because we don't have a real date field on `MonthlyXFormSubmissionCounter`
                # but we need to cast `year` and `month` as a date field to
                # compare it with `date_threshold`
                MonthlyXFormSubmissionCounter.objects.annotate(
                    date=Cast(
                        Concat(
                            F('year'), Value('-'), F('month'), Value('-'), 1
                        ),
                        DateField(),
                    )
                ).filter(user_id=user.pk, date__gte=date_threshold).delete()

                for xf in user.xforms.only('pk').iterator(chunk_size=chunks):
                    daily_counters = []
                    for values in (
                        xf.instances.filter(
                            date_created__date__gte=date_threshold
                        )
                        .values('date_created__date')
                        .annotate(num_of_submissions=Count('pk'))
                        .order_by('date_created__date')
                    ):
                        submission_date = values['date_created__date']
                        daily_counters.append(DailyXFormSubmissionCounter(
                            xform_id=xf.pk,
                            date=submission_date,
                            counter=values['num_of_submissions'],
                        ))
                        key = (
                            f'{submission_date.year}-{submission_date.month}'
                        )
                        total_submissions[key] += values['num_of_submissions']

                    if daily_counters:
                        if verbosity >= 2:
                            self.stdout.write(f'\tInserting daily counters data...')
                        DailyXFormSubmissionCounter.objects.bulk_create(
                            daily_counters, batch_size=chunks
                        )
                    elif verbosity >= 2:
                        self.stdout.write(f'\tNo daily counters data...')

                for key, total in total_submissions.items():
                    year, month = key.split('-')
                    monthly_counters.append(MonthlyXFormSubmissionCounter(
                        year=year,
                        month=month,
                        xform_id=xf.pk,
                        user_id=user.pk,
                        counter=total,
                    ))

                if monthly_counters:
                    if verbosity >= 2:
                        self.stdout.write(f'\tInserting monthly counters data...')
                    MonthlyXFormSubmissionCounter.objects.bulk_create(
                        monthly_counters, batch_size=chunks
                    )
                elif verbosity >= 2:
                    self.stdout.write(f'\tNo monthly counters data!')

                # Update user's profile (and lock the related row)
                updates = {
                    'submissions_suspended': False,
                    'counters_updates_status': 'complete',
                }
                UserProfile.objects.select_for_update().filter(
                    user_id=user.pk
                ).update(
                    metadata=ReplaceValues(
                        'metadata',
                        updates=updates,
                    ),
                )

        if verbosity >= 1:
            self.stdout.write(f'Done!')
