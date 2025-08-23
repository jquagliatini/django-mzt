import pytest
from uuid import uuid4
from dataclasses import dataclass
from datetime import timedelta, datetime
from django.contrib.sessions.backends.db import SessionStore

from timers.models import TimerSequence, TimerSequenceRun


@dataclass(frozen=True, kw_only=True)
class State:
    now: datetime
    sequence_run: TimerSequenceRun


@pytest.fixture
def state() -> State:
    now = datetime.fromisoformat("2025-05-01T10:00:00Z")

    s = SessionStore()
    s.create()
    session_key = s.session_key

    sequence = TimerSequence.create(
        now=now,
        session_key=session_key,
        name=("sequence_" + str(uuid4())),
        timers=[timedelta(minutes=10), timedelta(minutes=25)],
    )
    sequence_run = TimerSequenceRun.create(
        sequence=sequence, durations=[], session_key=session_key, now=now
    )

    return State(now=now, sequence_run=sequence_run)


@pytest.mark.django_db
def test_is_ended(state: State):
    assert state.sequence_run.is_ended(state.now + timedelta(minutes=10)) == False

    assert state.sequence_run.is_ended(state.now + timedelta(minutes=36)) == True


@pytest.mark.django_db
def test_is_paused(state: State):
    assert state.sequence_run.is_paused() == False

    state.sequence_run.pause(state.now + timedelta(minutes=5))

    paused = TimerSequenceRun.objects.get(pk=state.sequence_run.pk)
    assert paused.is_paused() == True
