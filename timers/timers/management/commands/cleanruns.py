from django.core.management.base import BaseCommand
from django.utils import timezone

from timers.models import TimerSequenceRun


class Command(BaseCommand):
    help = "Delete ended runs to save on storage space"

    def handle(self):
        now = timezone.now()
        runs = TimerSequenceRun.objects.filter(ends_at__lt=now).delete()
        self.stdout.write(
            self.style.SUCCESS(f"Deleted {len(runs)} obsolete runs, ended before {now}")
        )
