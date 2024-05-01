from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from reversion.models import Revision


def remove_old_revisions():
    days = settings.KOBOCAT_REVERSION_RETENTION_DAYS
    delete_queryset = Revision.objects.filter(
        date_created__lt=timezone.now() - timedelta(days=days),
    )
    while True:
        count, _ = delete_queryset.filter(pk__in=delete_queryset[:1000]).delete()
        if not count:
            break
