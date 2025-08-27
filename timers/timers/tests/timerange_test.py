from datetime import datetime, timedelta

from timers.lib.timerange import (
    DateTimePeriod,
    PausableTimerSequence,
)


def test_snapshot():
    pausable_sequence = PausableTimerSequence.from_timers(
        started_at=datetime.fromisoformat("2025-05-01T10:00:00Z"),
        durations=[timedelta(seconds=10), timedelta(seconds=20), timedelta(seconds=30)],
        pauses=[],
    )

    assert pausable_sequence.total_duration == timedelta(minutes=1)
    assert pausable_sequence.ends_at == datetime.fromisoformat("2025-05-01T10:01:00Z")

    snapshot = pausable_sequence.snapshot(
        datetime.fromisoformat("2025-05-01T10:00:25Z")
    )

    assert snapshot.past == [timedelta(seconds=10)]
    assert snapshot.current == timedelta(seconds=20)
    assert snapshot.future == [timedelta(seconds=30)]
    assert snapshot.remaining_time == timedelta(seconds=5)
    assert snapshot.total_remaining_time == timedelta(seconds=35)


def test_pauses():
    pausable_sequence = PausableTimerSequence.from_timers(
        started_at=datetime.fromisoformat("2025-05-01T10:00:00Z"),
        durations=[timedelta(seconds=60)],
        pauses=[
            DateTimePeriod(
                datetime.fromisoformat("2025-05-01T10:00:15Z"),
                datetime.fromisoformat("2025-05-01T10:00:20Z"),
            ),
            DateTimePeriod(
                datetime.fromisoformat("2025-05-01T10:00:25Z"),
                datetime.fromisoformat("2025-05-01T10:00:30Z"),
            ),
        ],
    )

    assert pausable_sequence.total_duration == timedelta(minutes=1, seconds=10)
    assert pausable_sequence.ends_at == datetime.fromisoformat("2025-05-01T10:01:10Z")

    snapshot = pausable_sequence.snapshot(
        datetime.fromisoformat("2025-05-01T10:00:40Z")
    )

    assert snapshot.remaining_time == timedelta(seconds=30)
    assert snapshot.total_remaining_time == timedelta(seconds=30)
