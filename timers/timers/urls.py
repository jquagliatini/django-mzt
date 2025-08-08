from django.urls import path
from timers.views import sequences


urlpatterns = [
    path("", view=sequences.listSequences, name="sequences"),
    path("sequence", view=sequences.createSequence, name="create_sequence"),
]
