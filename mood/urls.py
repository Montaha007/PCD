from django.urls import path
from .views import JournalEntryListCreateView, JournalEntryDetailView

urlpatterns = [
    path("entries/",       JournalEntryListCreateView.as_view(), name="journal-list-create"),
    path("entries/<int:pk>/", JournalEntryDetailView.as_view(),  name="journal-detail"),
]
