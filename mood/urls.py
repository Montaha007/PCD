from django.urls import path
from .views import JournalEntryListCreateView, JournalEntryDetailView, neo4j_status

urlpatterns = [
    path("entries/",          JournalEntryListCreateView.as_view(), name="journal-list-create"),
    path("entries/<int:pk>/", JournalEntryDetailView.as_view(),     name="journal-detail"),
    path("neo4j-status/",     neo4j_status,                         name="neo4j-status"),
]
