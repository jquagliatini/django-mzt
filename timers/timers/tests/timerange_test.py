from datetime import datetime, timedelta
from timers.lib.timerange import (
    DateTimePeriod,
    PausableTimerSequence,
    PausableTimerSequenceSnapshot,
)


def test_PausableTimerSequence():
    pausable_sequence = PausableTimerSequence.from_timers(
        started_at=datetime.fromisoformat("2025-05-01T10:00:00Z"),
        durations=[timedelta(seconds=10), timedelta(seconds=20), timedelta(seconds=30)],
        pauses=[
            DateTimePeriod(
                datetime.fromisoformat("2025-05-01T10:00:15Z"),
                datetime.fromisoformat("2025-05-01T10:00:20Z"),
            )
        ],
    )

    assert pausable_sequence.total_duration == timedelta(minutes=1, seconds=5)
    assert pausable_sequence.ends_at == datetime.fromisoformat("2025-05-01T10:01:05Z")

    snapshot = pausable_sequence.snapshot(datetime.fromisoformat("2025-05-01T10:00:21Z"))
    assert snapshot == PausableTimerSequenceSnapshot(
        past=[timedelta(seconds=10)],
        current=timedelta(seconds=20),
        future=[timedelta(seconds=30)],
        remaining_time=timedelta(seconds=14),
        total_remaining_time=timedelta(seconds=44),
    )
