from typing import cast
from datetime import datetime, timedelta
from django.db import models, transaction
from django.contrib.sessions.models import Session
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class TimerSequence(models.Model):
    name = models.TextField(null=False, blank=False)
    created_by = models.ForeignKey(Session, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def run(self, now: datetime = datetime.now()) -> "TimerSequenceRun":
        return TimerSequenceRun.create(self, now)

    @classmethod
    def create(
        cls,
        name: str,
        timers: list[timedelta],
        session_key: str,
        now: datetime = datetime.now(),
    ) -> "TimerSequence":
        assert len(timers) > 0, "expected a non empty list of timers"
 
        with transaction.atomic():
            session = Session.objects.get(session_key=session_key)
            sequence = TimerSequence(name=name, created_by=session, created_at=now)
            sequence.save()

            for index, duration in enumerate(timers):
                TimerSequenceDuration(
                    index=index, duration=duration, timer_sequence=sequence
                ).save()

            return sequence


class TimerSequenceDuration(models.Model):
    timer_sequence = models.ForeignKey(TimerSequence, on_delete=models.CASCADE)

    index = models.IntegerField()
    duration = models.DurationField()

    class Meta:
        unique_together = ["timer_sequence", "index"]
        ordering = ["index"]
        indexes = [models.Index(fields=["timer_sequence", "index"])]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(index__gte=0),  # type: ignore
                name="positive_index",
            ),
        ]


class TimerSequenceRun(models.Model):
    timer_sequence = models.ForeignKey(
        TimerSequence, null=True, on_delete=models.SET_NULL
    )
    timer_sequence_name = models.TextField()
    started_at = models.DateTimeField(null=True)

    @classmethod
    def create(cls, sequence: TimerSequence, now: datetime = datetime.now()):
        return TimerSequenceRun(
            timer_sequence=sequence, timer_sequence_name=sequence.name, started_at=now
        )

    def is_paused(self):
        running_pause = cast(
            TimerSequencePause | None,
            TimerSequencePause.objects.filter(
                timer_sequence=self, ended_at__isnull=True
            )[0],
        )

        return running_pause is not None

    def is_ended(self, now: datetime = datetime.now()) -> bool:
        if self.started_at is None or self.is_paused():
            return False

        total_duration: timedelta = timedelta()
        sequences = TimerSequenceDuration.objects.filter(
            timer_sequence=self.timer_sequence
        )
        for sequence in sequences:
            total_duration += sequence.duration

        pauses = TimerSequencePause.objects.filter(timer_sequence=self.timer_sequence)
        for pause in pauses:
            if pause.ended_at is None:
                continue
            total_duration += pause.ended_at - pause.started_at

        return self.started_at + total_duration > now

    def unpause(self, now: datetime):
        if self.is_ended(now):
            raise ValidationError(_("timer {id} ended") % {"id": self.pk})

        running_pause = TimerSequencePause.objects.get(
            timer_sequence=self, ended_at__isnull=True
        )

        running_pause.ended_at = now
        running_pause.save()

    def pause(self, now: datetime):
        if self.is_paused():
            raise ValidationError(_('timer "{id}" is already paused') % {"id": self.pk})

        if self.is_ended(now):
            raise ValidationError(_('timer "{id}" ended') % {"id": self.pk})

        TimerSequencePause.objects.create(started_at=now, timer_sequence=self).save()


class TimerSequencePause(models.Model):
    timer_sequence_run = models.ForeignKey(TimerSequenceRun, on_delete=models.CASCADE)

    started_at = models.DateTimeField(null=False, auto_now_add=True)
    ended_at = models.DateTimeField(null=True)

    class Meta:
        indexes = [
            models.Index(fields=["timer_sequence_run"]),
            models.Index(
                fields=["timer_sequence_run", "ended_at"],
                condition=models.Q(ended_at__isnull=True),
                name="pending_pause_idx",
            ),
        ]
