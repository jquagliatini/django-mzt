import json
from datetime import datetime, timedelta
from django.http import HttpRequest, HttpResponseNotFound
from django.shortcuts import redirect, render
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils.translation import gettext as _
from django.db.models import Prefetch
from django.db import transaction


from timers.forms import TimerSequenceDurationFormSet, TimerSequenceForm
from timers.models import TimerSequence, TimerSequenceRun


def listSequences(request: HttpRequest):
    session_key = request.session.session_key
    if not session_key:
        request.session.create()
        request.session.save()
        session_key = request.session.session_key

    paginator = Paginator(
        TimerSequence.objects.filter(created_by=session_key).prefetch_related('durations'),
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
                name=name, timers=timers, session_key=request.session.session_key
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
    if request.method != 'POST':
        return HttpResponseNotFound()

    sequence = TimerSequence.objects.get(pk=sequence_id)
    run = sequence.run(datetime.now())

    return redirect('detail_sequence_run', sequence_id=sequence_id, run_id=run.pk)

@transaction.atomic
def detail_sequence_run(request: HttpRequest, sequence_id: int, run_id: int):
    session_key = request.session.session_key
    if not session_key:
        request.session.create()
        request.session.save()
        session_key = request.session.session_key

    sequence = TimerSequence.objects.filter(pk=sequence_id, created_by=session_key).prefetch_related(
        Prefetch("runs", queryset=TimerSequenceRun.objects.filter(pk=run_id))
    ).get()

    run: TimerSequenceRun = sequence.runs.get() # type: ignore

    if request.method == 'POST':
        run.toggle(datetime.now()) # type: ignore
        id = run.pk # type: ignore
        run = TimerSequenceRun.objects.get(pk=id)
    
    timers = [x.duration for x in sequence.durations.all()] # type: ignore
    pauses = json.dumps([{ 'startedAt': x.started_at, 'endedAt': x.ended_at } for x in run.pauses.all()]) # type: ignore

    return render(request, 'sequences/run.html', { 'run': run, 'pauses': pauses, 'timers': timers })
