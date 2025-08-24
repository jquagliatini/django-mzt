import pytest
from dataclasses import dataclass
from uuid import uuid4
from datetime import timedelta, datetime
from django.contrib.sessions.models import Session
from django.contrib.sessions.backends.db import SessionStore

from timers.lib.projections import TimerProjection, TimerState
from timers.models import (
    TimerSequence,
    TimerSequencePause,
    TimerSequenceRun,
)


@dataclass(frozen=True, kw_only=True)
class State:
    now: datetime
    sequence: TimerSequence
    sequence_run: TimerSequenceRun
    pauses: list[TimerSequencePause]


@pytest.fixture
def state():
    now = datetime.fromisoformat("2025-05-01T10:00:00Z")
    s = SessionStore()
    s.create()
    created_by = Session.objects.get(pk=s.session_key)

    sequence = TimerSequence(name="sequence_" + str(uuid4()))
    sequence_run = TimerSequenceRun(
        timer_sequence=sequence,
        created_by=created_by,
        timer_sequence_durations=[
            timedelta(seconds=10),
            timedelta(seconds=20),
            timedelta(seconds=30),
        ],
        started_at=now + timedelta(minutes=5),
    )
    pauses = [
        TimerSequencePause(
            timer_sequence_run=sequence_run,
            started_at=(now + timedelta(minutes=5, seconds=5)),
            ended_at=(now + timedelta(minutes=5, seconds=10)),
        )
    ]

    return State(
        now=now,
        pauses=pauses,
        sequence=sequence,
        sequence_run=sequence_run,
    )


@pytest.mark.django_db
def test_full_state(state: State):
    projection = TimerProjection.from_timer_sequence_run(
        now=state.now + timedelta(minutes=5, seconds=16),
        sequence_run=state.sequence_run,
        pauses=state.pauses,
    )

    assert projection.state == TimerState.running
    assert projection.remaining_time == timedelta(seconds=19)
    assert projection.total_remaining_time == timedelta(seconds=49)

    assert projection.past_timers == [timedelta(seconds=10)]
    assert projection.current_timer == timedelta(seconds=20)
    assert projection.future_timers == [timedelta(seconds=30)]

    assert projection.ends_at == datetime.fromisoformat("2025-05-01T10:06:05Z")


@pytest.mark.django_db
def test_pause_state(state: State):
    state.pauses.append(
        TimerSequencePause(
            timer_sequence_run=state.sequence_run,
            started_at=state.now + timedelta(minutes=5, seconds=15),
            ended_at=None,
        )
    )

    projection = TimerProjection.from_timer_sequence_run(
        now=state.now + timedelta(minutes=5, seconds=16),
        sequence_run=state.sequence_run,
        pauses=state.pauses,
    )

    assert projection.state == TimerState.paused
    assert projection.ends_at == None


@pytest.mark.django_db
def test_ended_state(state: State):
    projection = TimerProjection.from_timer_sequence_run(
        now=state.now + timedelta(minutes=10),
        sequence_run=state.sequence_run,
        pauses=state.pauses,
    )

    assert projection.state == TimerState.ended
    assert projection.ends_at == datetime.fromisoformat("2025-05-01T10:06:05Z")
