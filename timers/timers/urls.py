from django.urls import path
from timers.views import sequences


urlpatterns = [
    path("", view=sequences.listSequences, name="sequences"),
    path("sequences", view=sequences.createSequence, name="create_sequence"),
    path(
        "sequences/<int:sequence_id>/runs",
        view=sequences.run_sequence,
        name="run_sequence",
    ),
    path(
        "sequences/<int:sequence_id>/runs/<int:run_id>",
        view=sequences.detail_sequence_run,
        name="detail_sequence_run",
    ),
]
