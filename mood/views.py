from rest_framework import generics, permissions

from .models import JournalEntry
from .serializers import JournalEntryCreateSerializer, JournalEntrySerializer


def trigger_ai_analysis(entry_id: int) -> None:
    # Will be wired up once the mood AI pipeline is ready:
    # from ai.services import analyze_journal_entry
    # analyze_journal_entry(entry_id)
    pass


class JournalEntryListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return JournalEntry.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return JournalEntryCreateSerializer
        return JournalEntrySerializer

    def perform_create(self, serializer):
        entry = serializer.save(user=self.request.user, status=JournalEntry.Status.PENDING)
        trigger_ai_analysis(entry.id)


class JournalEntryDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class   = JournalEntrySerializer

    def get_queryset(self):
        return JournalEntry.objects.filter(user=self.request.user)
