from datetime import timedelta
from typing import Iterable
from django.http import HttpRequest, HttpResponseNotFound
from django.shortcuts import redirect, render
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils import timezone
from django.utils.translation import gettext as _
from django.db import transaction


from timers.forms import TimerSequenceDurationFormSet, TimerSequenceForm
from timers.models import TimerSequence, TimerSequencePause, TimerSequenceRun
from timers.lib.projections import TimerProjection


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

        print("DEBUG")
        print(request.POST)
        print([x["duration"].value() for x in formset])

        if form.is_valid() and formset.is_valid():
            name: str = form["name"].value()
            durations: list[str] = [x["duration"].value() for x in formset]

            timers: list[timedelta] = []
            for duration in durations:
                match tuple(map(float, duration.split(":"))):
                    case (hours, minutes, seconds):
                        timers.append(
                            timedelta(hours=hours, minutes=minutes, seconds=seconds)
                        )
                    case (minutes, seconds):
                        timers.append(timedelta(minutes=minutes, seconds=seconds))
                    case (seconds,):
                        timers.append(timedelta(seconds=seconds))
                    case _:
                        pass

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

    response = render(request, "sequences/run_static.html", {"timer": timer})
    response["Cache-Control"] = "no-store"

    return response
