# audio/urls.py
from django.urls import path

from audio.views import (
    get_personalised_recommendation,
    get_manual_recommendation,
    list_disorders,
)

app_name = "audio"

urlpatterns = [
    # Default — what the audio page calls. Reads from the latest DailyProgress.
    path("recommendation/",        get_personalised_recommendation, name="recommendation"),

    # Debug / "explore other tracks" UI. Takes ?disorder=anxiety.
    path("recommendation/manual/", get_manual_recommendation,       name="recommendation-manual"),

    # Enum dropdown.
    path("disorders/",             list_disorders,                  name="disorders"),
]