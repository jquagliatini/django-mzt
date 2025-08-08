from django.http import HttpRequest
from django.shortcuts import render

from timers.forms import TimerSequenceDurationFormSet, TimerSequenceForm

def listSequences(request: HttpRequest):
  return render(request, "sequences/list.html")

def createSequence(request: HttpRequest):
    form = TimerSequenceForm()
    formset = TimerSequenceDurationFormSet()

    return render(request, "sequences/create.html", { "form": form, "formset": formset })