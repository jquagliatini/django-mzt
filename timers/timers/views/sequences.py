from datetime import timedelta
from django.http import HttpRequest
from django.shortcuts import redirect, render
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils.translation import gettext as _

from timers.forms import TimerSequenceDurationFormSet, TimerSequenceForm
from timers.models import TimerSequence

def listSequences(request: HttpRequest):
  session_key = request.session.session_key
  if not session_key:
      request.session.create()
      request.session.save()
      session_key = request.session.session_key

  paginator = Paginator(TimerSequence.objects.filter(created_by=session_key), 25)
  page = request.GET.get('page')
  sequences = paginator.get_page(page)

  return render(request, "sequences/list.html", { "sequences": sequences })

def createSequence(request: HttpRequest):
    if not request.session.session_key:
       request.session.create()
       request.session.save()

    if request.method == 'POST':
       form = TimerSequenceForm(request.POST)
       formset = TimerSequenceDurationFormSet(request.POST)

       if form.is_valid() and formset.is_valid():
          name: str = form['name'].value()
          durations: list[str] = [x['duration'].value() for x in formset]

          timers: list[timedelta] = []
          for duration in durations:
              match tuple(map(float, duration.split(':'))):
                  case (hours, minutes, seconds):
                      timers.append(timedelta(hours=hours, minutes=minutes, seconds=seconds))
                  case (minutes, seconds):
                      timers.append(timedelta(minutes=minutes, seconds=seconds))
                  case (seconds,):
                      timers.append(timedelta(seconds=seconds))
                  case _:
                    pass

          TimerSequence.create(name=name, timers=timers, session_key=request.session.session_key)
          messages.add_message(request, messages.SUCCESS, _('timer sequence "{name}" created successfully') % { "name": name })

          return redirect('sequences', preserve_request=True)
       else:
          messages.add_message(request, messages.ERROR, _('There was an issue with your timer sequence'))

    else:
      form = TimerSequenceForm()
      formset = TimerSequenceDurationFormSet()

    return render(request, "sequences/create.html", { "form": form, "formset": formset })