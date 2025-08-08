from django import forms

class _TimerSequenceDurationForm(forms.Form):
  template_name_div = 'sequences/formsets/form.html'
  duration = forms.DurationField()

TimerSequenceDurationFormSet = forms.formset_factory(
  _TimerSequenceDurationForm,
  max_num=100,
  validate_max=True,
)

class TimerSequenceForm(forms.Form):
  name = forms.CharField(max_length=2048)
