from django.urls import path
from timers.views import sequences


urlpatterns = [
    path("", view=sequences.listSequences, name="sequences"),
    path("sequences", view=sequences.createSequence, name="create_sequence"),
    path("sequences/<int:id>", view=sequences.createSequence, name="start_sequence"),
]
