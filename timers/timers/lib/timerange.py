from typing import Iterable, Iterator
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass(frozen=True)
class DateTimePeriod:
    start: datetime
    end: datetime

    @property
    def duration(self) -> timedelta:
        return self.end - self.start

    def __post_init__(self):
        assert self.start < self.end


@dataclass(frozen=True, kw_only=True)
class PausedDateTimePeriod(DateTimePeriod):
    timer: DateTimePeriod
    pause: DateTimePeriod | None = None

    def add_pause(self, pause: DateTimePeriod) -> "PausedDateTimePeriod":
        assert self.pause is None

        return PausedDateTimePeriod(
            pause=pause,
            timer=self.timer,
            start=self.start,
            end=self.start + (self.duration + pause.duration),
        )

    @classmethod
    def from_datetime_period(cls, period: DateTimePeriod):
        return PausedDateTimePeriod(start=period.start, end=period.end, timer=period)


@dataclass(frozen=True, kw_only=True)
class PausableTimerSequenceSnapshot:
    current: timedelta | None = None
    past: list[timedelta]
    future: list[timedelta]
    remaining_time: timedelta
    total_remaining_time: timedelta


@dataclass(frozen=True, kw_only=True)
class PausableTimerSequence:
    pausable_timers: list[PausedDateTimePeriod]

    @property
    def ends_at(self) -> datetime:
        return self.pausable_timers[-1].end

    @property
    def total_duration(self) -> timedelta:
        total_duration = timedelta()
        for period in self.pausable_timers:
            total_duration += period.duration

        return total_duration

    def snapshot(self, now: datetime) -> PausableTimerSequenceSnapshot:
        past: list[timedelta] = []
        future: list[timedelta] = []
        current: timedelta | None = None

        remaining_time = timedelta()
        total_remaining_time = timedelta()

        for pausable in self.pausable_timers:
            if now > pausable.end:
                past.append(pausable.timer.duration)
            elif now < pausable.start:
                future.append(pausable.timer.duration)
                total_remaining_time += pausable.duration
            elif current is None and pausable.start <= now <= pausable.end:
                current = pausable.timer.duration
                remaining_time = pausable.end - now
                total_remaining_time += pausable.end - now

        return PausableTimerSequenceSnapshot(
            past=past,
            current=current,
            future=future,
            remaining_time=remaining_time,
            total_remaining_time=total_remaining_time,
        )

    @classmethod
    def from_timers(
        cls,
        started_at: datetime,
        durations: Iterable[timedelta],
        pauses: Iterable[DateTimePeriod],
    ) -> "PausableTimerSequence":
        usable_pauses = [pause for pause in pauses]

        elapsed_time = timedelta()
        pausable_timers: list[PausedDateTimePeriod] = []

        for duration in durations:
            elapsed_time += duration
            end = started_at + elapsed_time
            start = end - duration

            timer = PausedDateTimePeriod.from_datetime_period(
                DateTimePeriod(start, end)
            )

            found_pause = False
            for pause in usable_pauses:
                if pause.start <= timer.end:
                    found_pause = True
                    pausable_timers.append(timer.add_pause(pause))
                    elapsed_time += pause.duration
                    usable_pauses.remove(pause)
                    break

            if not found_pause:
                pausable_timers.append(timer)

        return cls(pausable_timers=pausable_timers)

    def __post_init__(self):
        assert len(self.pausable_timers) > 0

    def __iter__(self) -> Iterator[DateTimePeriod]:
        return iter(self.pausable_timers)
