from datetime import datetime, timedelta
from typing import Any, Iterable
from django.db import models, transaction
from django.contrib.sessions.models import Session
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class TimerSequence(models.Model):
    name = models.TextField(null=False, blank=False)
    created_by = models.ForeignKey(Session, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def run(self, now: datetime, session_key: str) -> "TimerSequenceRun":
        durations: Iterable["TimerSequenceDuration"] = (
            TimerSequenceDuration.objects.filter(timer_sequence=self)
            .order_by("index")
            .all()
        )
        return TimerSequenceRun.create(self, durations, now, session_key=session_key)

    def update_timers(self, timers: Iterable[timedelta]):
        with transaction.atomic():
            TimerSequenceDuration.objects.filter(timer_sequence=self).delete()
            for index, duration in enumerate(timers):
                TimerSequenceDuration(
                    index=index, duration=duration, timer_sequence=self
                ).save()

    @classmethod
    def create(
        cls,
        name: str,
        timers: list[timedelta],
        session_key: str,
        now: datetime,
    ) -> "TimerSequence":
        assert len(timers) > 0, "expected a non empty list of timers"

        with transaction.atomic():
            session = Session.objects.get(session_key=session_key)
            sequence = TimerSequence(name=name, created_by=session, created_at=now)
            sequence.save()

            sequence.update_timers(timers)

            return sequence


class TimerSequenceDuration(models.Model):
    timer_sequence = models.ForeignKey(
        TimerSequence, on_delete=models.CASCADE, related_name="durations"
    )

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
    class TimerSequenceDurationsField(models.Field):  # type: ignore
        def db_type(self, connection: Any):
            return "text"

        def from_db_value(
            self, value: str | None, _expression: Any, _connection: Any
        ) -> list[timedelta]:
            return self.to_python(value) if value else []

        def get_prep_value(self, value: list[timedelta] | None) -> Any:
            return (
                ",".join(str(int(x / timedelta(milliseconds=1))) for x in value)
                if value
                else ""
            )

        def to_python(self, value: list[timedelta] | str | None) -> list[timedelta]:
            if isinstance(value, list) and all(isinstance(x, timedelta) for x in value):  # type: ignore
                return value
            if isinstance(value, str):
                return [timedelta(milliseconds=int(x)) for x in value.split(",")]
            if value is None:
                return []

            raise ValidationError("Invalid durations")

    created_by = models.ForeignKey(Session, on_delete=models.CASCADE, editable=False)
    timer_sequence = models.ForeignKey(
        TimerSequence, null=True, on_delete=models.SET_NULL, related_name="runs"
    )
    timer_sequence_name = models.TextField()
    started_at = models.DateTimeField(null=True)
    timer_sequence_durations = TimerSequenceDurationsField(
        blank=False, null=False, editable=False
    )
    ends_at = models.DateTimeField(null=True, default=None, editable=False)

    class Meta:
        indexes = [models.Index(fields=["ends_at"])]

    @classmethod
    def create(
        cls,
        sequence: TimerSequence,
        durations: Iterable[TimerSequenceDuration],
        now: datetime,
        session_key: str,
    ):
        run = TimerSequenceRun(
            timer_sequence=sequence,
            timer_sequence_name=sequence.name,
            started_at=now,
            timer_sequence_durations=[d.duration for d in durations],
            created_by=Session.objects.get(pk=session_key),
        )
        run.ends_at = run._get_ends_at(durations, [])
        run.save()

        return run

    def is_paused(self):
        try:
            TimerSequencePause.objects.filter(
                timer_sequence_run=self, ended_at__isnull=True
            ).get()
            return True
        except TimerSequencePause.DoesNotExist:
            return False

    def _get_ends_at(
        self,
        durations: Iterable[TimerSequenceDuration] | Iterable[timedelta],
        pauses: Iterable["TimerSequencePause"],
    ) -> datetime | None:
        if self.started_at is None:
            return None

        total_duration: timedelta = timedelta()
        for sequence in durations:
            total_duration += (
                sequence if isinstance(sequence, timedelta) else sequence.duration
            )

        for pause in pauses:
            if pause.ended_at is None:
                continue
            total_duration += pause.ended_at - pause.started_at

        return self.started_at + total_duration

    def is_ended(self, now: datetime) -> bool:
        if self.started_at is None or self.is_paused():
            return False

        ends_at = self._get_ends_at(
            durations=TimerSequenceDuration.objects.filter(
                timer_sequence=self.timer_sequence
            ),
            pauses=TimerSequencePause.objects.filter(timer_sequence_run=self).all(),
        )

        return ends_at <= now if ends_at is not None else False

    def toggle(self, now: datetime):
        if self.is_ended(now):
            return

        if self.is_paused():
            return self.unpause(now)

        return self.pause(now)

    def unpause(self, now: datetime):
        if self.is_ended(now):
            raise ValidationError(_("timer {id} ended") % {"id": self.pk})

        running_pause = TimerSequencePause.objects.get(
            timer_sequence_run=self, ended_at__isnull=True
        )

        running_pause.ended_at = now
        running_pause.save()

        pauses = TimerSequencePause.objects.filter(timer_sequence_run=self).all()
        self.ends_at = self._get_ends_at(
            self.timer_sequence_durations,  # type: ignore
            pauses,
        )
        self.save()

    def pause(self, now: datetime):
        if self.is_paused():
            raise ValidationError(_('timer "{id}" is already paused') % {"id": self.pk})

        if self.is_ended(now):
            raise ValidationError(_('timer "{id}" ended') % {"id": self.pk})

        TimerSequencePause.objects.create(
            started_at=now, timer_sequence_run=self
        ).save()

        self.ends_at = None
        self.save()


class TimerSequencePause(models.Model):
    timer_sequence_run = models.ForeignKey(
        TimerSequenceRun, on_delete=models.CASCADE, related_name="pauses"
    )

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
