from rest_framework import generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from .models import JournalEntry
from .serializers import JournalEntryCreateSerializer, JournalEntrySerializer


def trigger_ai_analysis(entry: JournalEntry) -> None:
    import traceback
    try:
        from ai.services import analyze_journal
        entry.status = JournalEntry.Status.PROCESSING
        entry.save(update_fields=["status"])

        result = analyze_journal(entry.content)
        entry.predicted_mood = result["predicted_label"]
        entry.analysis_text  = result["analysis_text"]
        entry.status         = JournalEntry.Status.COMPLETED
    except Exception:
        traceback.print_exc()
        entry.status = JournalEntry.Status.FAILED
    finally:
        entry.save(update_fields=["predicted_mood", "analysis_text", "status"])


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
        trigger_ai_analysis(entry)


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def neo4j_status(_request):
    try:
        from ai.client import get_neo4j_driver
        driver = get_neo4j_driver()
        with driver.session() as session:
            session.run("RETURN 1")
        return Response({"neo4j": "ok"})
    except Exception as e:
        return Response({"neo4j": "unavailable", "error": str(e)}, status=503)


class JournalEntryDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class   = JournalEntrySerializer

    def get_queryset(self):
        return JournalEntry.objects.filter(user=self.request.user)
