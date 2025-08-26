from typing import TypeVar
from django import forms
import timers.lib.classes as c

_BaseFormT = TypeVar("_BaseFormT", bound=forms.BaseForm)


class _TimerSequenceDurationForm(forms.Form):
    duration = forms.DurationField()


class _BaseTimerSequenceDurationFormSet(forms.BaseFormSet):  # type: ignore
    template_name = "sequences/formsets/form.html"


TimerSequenceDurationFormSet = forms.formset_factory(
    _TimerSequenceDurationForm,
    formset=_BaseTimerSequenceDurationFormSet,
    max_num=100,
    validate_max=True,
)


class TimerSequenceForm(forms.Form):
    name = forms.CharField(
        label="",
        label_suffix="",
        max_length=2048,
        widget=forms.TextInput(attrs={"class": c.input()}),
    )
