import enum
from typing import Any, Iterable, cast
from dataclasses import dataclass
from datetime import timedelta, datetime

from timers.models import TimerSequencePause, TimerSequenceRun
from timers.lib.timerange import DateTimePeriod, PausableTimerSequence


class TimerState(enum.StrEnum):
    running = "running"
    paused = "paused"
    ended = "ended"


@dataclass
class TimerProjection:
    state: TimerState
    current_timer: timedelta | None
    remaining_time: timedelta
    total_remaining_time: timedelta
    past_timers: list[timedelta]
    future_timers: list[timedelta]
    ends_at: datetime | None = None

    @property
    def remaining_time_radians(self) -> float:
        if not self.current_timer:
            return 0.0

        return (self.remaining_time / self.current_timer) * 360

    def to_json(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "remainingTime": int(self.remaining_time / timedelta(milliseconds=1)),
            "totalRemainingTime": int(
                self.total_remaining_time / timedelta(milliseconds=1)
            ),
            "currentTimer": int(self.current_timer / timedelta(milliseconds=1))
            if self.current_timer is not None
            else None,
            "pastTimers": [
                int(x / timedelta(milliseconds=1)) for x in self.past_timers
            ],
            "futureTimers": [
                int(x / timedelta(milliseconds=1)) for x in self.future_timers
            ],
        }

    @classmethod
    def from_timer_sequence_run(
        cls,
        now: datetime,
        sequence_run: TimerSequenceRun,
        pauses: Iterable[TimerSequencePause],
    ) -> "TimerProjection":
        assert sequence_run.started_at is not None, (
            f"sequence {sequence_run.pk} was not started"
        )

        usable_pauses: list[DateTimePeriod] = []
        is_paused = False
        for pause in pauses:
            if pause.ended_at is None:
                is_paused = True
                continue

            usable_pauses.append(DateTimePeriod(pause.started_at, pause.ended_at))

        durations: list[timedelta] = cast(
            list[timedelta],
            sequence_run.timer_sequence_durations,  # type: ignore
        )
        pausable_timer_sequence = PausableTimerSequence.from_timers(
            sequence_run.started_at,
            durations,
            usable_pauses,
        )
        projection = pausable_timer_sequence.split(now)

        state = TimerState.running
        if is_paused:
            state = TimerState.paused
        elif projection.total_remaining_time <= timedelta():
            state = TimerState.ended

        ends_at: datetime | None = None
        if state == TimerState.ended:
            ends_at = sequence_run.started_at + pausable_timer_sequence.total_duration
        elif state == TimerState.running:
            ends_at = now + projection.total_remaining_time

        return cls(
            state=state,
            ends_at=ends_at,
            past_timers=projection.past,
            future_timers=projection.future,
            current_timer=projection.current,
            remaining_time=projection.remaining_time,
            total_remaining_time=projection.total_remaining_time,
        )
