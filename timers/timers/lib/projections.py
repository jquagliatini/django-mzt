import enum
from typing import Any, Iterable, cast
from dataclasses import dataclass
from datetime import timedelta, datetime
from timers.models import TimerSequencePause, TimerSequenceRun


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
        assert sequence_run.started_at is not None, f"sequence {sequence_run.pk} was not started"

        is_paused = False
        total_pause_time = timedelta()
        for pause in pauses:
            if pause.ended_at is None:
                is_paused = True
                now = pause.started_at
                continue

            total_pause_time += pause.ended_at - pause.started_at

        remaining_time = timedelta()
        total_remaining_time = timedelta()

        current_timer: timedelta | None = None
        past_timers: list[timedelta] = []
        future_timers: list[timedelta] = []

        # elapsed_time = now - sequence_run.started_at - total_pause_time
        consumable_time = now - sequence_run.started_at + total_pause_time

        zero = timedelta()
        total_timers_duration = timedelta()

        for timer_duration in cast(list[timedelta], sequence_run.timer_sequence_durations):  # type: ignore
            total_timers_duration += timer_duration

            if consumable_time > zero:
                if timer_duration > consumable_time:
                    current_timer = timer_duration
                    remaining_time = timer_duration - consumable_time
                    total_remaining_time = timer_duration - consumable_time
                else:
                    past_timers.append(timer_duration)

            else:
                future_timers.append(timer_duration)
                total_remaining_time += timer_duration

            consumable_time -= timer_duration

        ends_at = sequence_run.started_at + total_timers_duration + total_pause_time
        is_ended = ends_at <= now

        state = TimerState.running
        if is_paused:
            ends_at = None
            state = TimerState.paused
        elif is_ended:
            state = TimerState.ended
            remaining_time = timedelta()
            total_remaining_time = timedelta()

        return cls(
            state=state,
            ends_at=ends_at,
            past_timers=past_timers,
            future_timers=future_timers,
            current_timer=current_timer,
            remaining_time=remaining_time,
            total_remaining_time=total_remaining_time,
        )
