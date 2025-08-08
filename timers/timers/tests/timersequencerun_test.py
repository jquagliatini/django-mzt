from uuid import uuid4
from django.test import TestCase
from datetime import timedelta, datetime
from django.contrib.sessions.backends.db import SessionStore

from timers.models import TimerSequence, TimerSequenceRun


class TimerSequenceRunTest(TestCase):
    now: datetime
    sequence_run: TimerSequenceRun

    def setUp(self):
        self.now = datetime.fromisoformat("2025-05-01T10:00:00Z")

        s = SessionStore()
        s.create()
        session_key = s.session_key

        sequence = TimerSequence.create(
            now=self.now,
            session_key=session_key,
            name=("sequence_" + str(uuid4())),
            timers=[timedelta(minutes=10), timedelta(minutes=25)],
        )
        self.sequence_run = TimerSequenceRun.create(sequence=sequence, now=self.now)

    def test_is_ended(self):
        self.assertFalse(self.sequence_run.is_ended(self.now + timedelta(minutes=10)))

        self.assertTrue(self.sequence_run.is_ended(self.now + timedelta(minutes=36)))

    def test_is_paused(self):
        self.assertFalse(self.sequence_run.is_paused())

        self.sequence_run.pause(self.now + timedelta(minutes=5))

        paused = TimerSequenceRun.objects.get(pk=self.sequence_run.pk)
        self.assertTrue(paused.is_paused())
