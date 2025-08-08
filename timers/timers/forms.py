from django import forms
import timers.lib.classes as c


class _TimerSequenceDurationForm(forms.Form):
    template_name_div = "sequences/formsets/form.html"
    duration = forms.DurationField()


TimerSequenceDurationFormSet = forms.formset_factory(
    _TimerSequenceDurationForm,
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
