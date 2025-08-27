from typing import Iterable

from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.http import HttpRequest, HttpResponse, HttpResponseNotFound
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_duration
from django.utils.translation import gettext as _

from timers.forms import TimerSequenceDurationFormSet, TimerSequenceForm
from timers.lib.projections import TimerProjection
from timers.models import (
    TimerSequence,
    TimerSequenceDuration,
    TimerSequencePause,
    TimerSequenceRun,
)


def listSequences(request: HttpRequest):
    session_key = request.session.session_key
    if not session_key:
        request.session.create()
        request.session.save()
        session_key = request.session.session_key

    paginator = Paginator(
        TimerSequence.objects.filter(created_by=session_key).prefetch_related(
            "durations"
        ),
        25,
    )
    page = request.GET.get("page")
    sequences = paginator.get_page(page)

    return render(request, "sequences/list.html", {"sequences": sequences})


def createSequence(request: HttpRequest):
    if not request.session.session_key:
        request.session.create()
        request.session.save()

    if request.method == "POST":
        form = TimerSequenceForm(request.POST)
        formset = TimerSequenceDurationFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            name: str = form["name"].value()
            timers = [
                duration
                for x in formset
                if (duration := parse_duration(x["duration"].value())) is not None
            ]

            TimerSequence.create(
                name=name,
                timers=timers,
                session_key=request.session.session_key,
                now=timezone.now(),
            )
            messages.add_message(
                request,
                messages.SUCCESS,
                _('timer sequence "{name}" created successfully') % {"name": name},
            )

            return redirect("sequences", preserve_request=True)
        else:
            messages.add_message(
                request,
                messages.ERROR,
                _("There was an issue with your timer sequence"),
            )

    else:
        form = TimerSequenceForm()
        formset = TimerSequenceDurationFormSet()

    return render(request, "sequences/create.html", {"form": form, "formset": formset})


@transaction.atomic
def update_sequence(request: HttpRequest, sequence_id: int) -> HttpResponse:
    sequence = TimerSequence.objects.get(pk=sequence_id)
    durations = TimerSequenceDuration.objects.filter(timer_sequence=sequence)

    if request.method == "POST":
        form = TimerSequenceForm(request.POST, initial={"name": sequence.name})
        formset = TimerSequenceDurationFormSet(
            request.POST, initial=[{"duration": x.duration} for x in durations]
        )

        if form.is_valid() and formset.is_valid():
            if form.has_changed():
                sequence.name = form["name"].value()
                sequence.save()

            if formset.has_changed():
                sequence.update_timers(
                    duration
                    for x in formset
                    if (duration := parse_duration(x["duration"].value())) is not None
                )

            messages.add_message(
                request,
                level=messages.SUCCESS,
                message=_('"{name}" updated successfully')
                % {"name": form["name"].value()},
            )
            return redirect("sequences", preserve_request=True)

        else:
            messages.add_message(
                request,
                level=messages.ERROR,
                message=_('Impossible to update "{name}"') % {"name": sequence.name},
            )

    else:
        form = TimerSequenceForm(data={"name": sequence.name})
        formset = TimerSequenceDurationFormSet(
            initial=[{"duration": x.duration} for x in durations]
        )

    return render(
        request,
        "sequences/update.html",
        {"form": form, "formset": formset, "sequence": sequence},
    )


def run_sequence(request: HttpRequest, sequence_id: int):
    if request.method != "POST":
        return HttpResponseNotFound()

    session_key = request.session.session_key
    if not session_key:
        request.session.create()
        request.session.save()
        session_key = request.session.session_key

    sequence = TimerSequence.objects.get(pk=sequence_id)
    run = sequence.run(timezone.now(), session_key)

    return redirect("detail_sequence_run", sequence_id=sequence_id, run_id=run.pk)


@transaction.atomic
def detail_sequence_run(request: HttpRequest, sequence_id: int, run_id: int):
    session_key = request.session.session_key
    if not session_key:
        request.session.create()
        request.session.save()
        session_key = request.session.session_key

    run = TimerSequenceRun.objects.get(
        pk=run_id, timer_sequence_id=sequence_id, created_by=session_key
    )

    if request.method == "POST":
        run.toggle(timezone.now())  # type: ignore
        run.refresh_from_db()

    pauses: Iterable[TimerSequencePause] = TimerSequencePause.objects.filter(
        timer_sequence_run=run
    ).all()
    timer = TimerProjection.from_timer_sequence_run(
        now=timezone.now(), pauses=pauses, sequence_run=run
    )

    response = render(request, "sequences/run.html", {"timer": timer})
    response["Cache-Control"] = "no-store"

    return response
