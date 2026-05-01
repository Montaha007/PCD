# ai/urls.py
# Wire into the project's main URLconf:
#   path("api/ai/", include("ai.urls")),
from django.urls import path

from ai.views import (
    JournalSubmissionView,
    ProgressDetailView,
    RerunView,
    TodayProgressView,
)

app_name = "ai"

urlpatterns = [
    # Drives the progress bar (poll every ~3s)
    path("progress/today/", TodayProgressView.as_view(), name="progress-today"),

    # Journal text submission (the 3rd input)
    path("journal/", JournalSubmissionView.as_view(), name="journal"),

    # Inspect / rerun a specific row
    path("runs/<uuid:id>/",       ProgressDetailView.as_view(), name="run-detail"),
    path("runs/<uuid:id>/rerun/", RerunView.as_view(),          name="run-rerun"),
]