# ai/views.py
# ============================================================================
# Three endpoints:
#
#   GET  /api/ai/progress/today/    → drives the progress bar
#   POST /api/ai/journal/           → record today's journal text
#   GET  /api/ai/runs/<uuid>/       → inspect a specific row
#   POST /api/ai/runs/<uuid>/rerun/ → re-run the pipeline for a finished day
# ============================================================================
from __future__ import annotations

from rest_framework import permissions, status
from rest_framework.generics import RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from ai.models import DailyProgress
from ai.progress import (
    get_today_progress,
    record_journal,
    request_rerun,
)
from ai.serializers import (
    DailyProgressSerializer,
    JournalSubmissionSerializer,
)


class TodayProgressView(APIView):
    """
    GET /api/ai/progress/today/
    Returns the row that drives the front-end progress bar. If the user has
    submitted nothing today, returns an empty stub at 0%.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        progress = get_today_progress(request.user)

        if progress is None:
            return Response({
                "id":                  None,
                "date":                None,
                "status":              DailyProgress.Status.WAITING,
                "progress_percent":    0,
                "sleep_submitted":     False,
                "lifestyle_submitted": False,
                "journal_submitted":   False,
                "submitted_count":     0,
                "all_submitted":       False,
                "pipeline_metadata":   None,
                "final_output":        None,
                "reasoning_report":    None,
                "unified_profile":     None,
                "error_message":       "",
                "current_step": 0, 
                "total_steps": 4,
            })

        return Response(DailyProgressSerializer(progress).data)


class JournalSubmissionView(APIView):
    """
    POST /api/ai/journal/   { "text": "..." }
    Records today's journal text. If sleep + lifestyle were already submitted,
    the pipeline auto-starts in the background.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = JournalSubmissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        text = serializer.validated_data["text"]

        progress = record_journal(request.user, text)
        return Response(
            DailyProgressSerializer(progress).data,
            status=status.HTTP_201_CREATED,
        )


class ProgressDetailView(RetrieveAPIView):
    """GET /api/ai/runs/<uuid>/  — fetch any DailyProgress row by id."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class   = DailyProgressSerializer
    lookup_field       = "id"

    def get_queryset(self):
        return DailyProgress.objects.filter(user=self.request.user)


class RerunView(APIView):
    """POST /api/ai/runs/<uuid>/rerun/  — kick off a fresh analysis."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        try:
            progress = DailyProgress.objects.get(id=id, user=request.user)
        except DailyProgress.DoesNotExist:
            return Response(
                {"error": "Not found."}, status=status.HTTP_404_NOT_FOUND,
            )

        try:
            progress = request_rerun(progress)
        except ValueError as exc:
            return Response(
                {"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            DailyProgressSerializer(progress).data,
            status=status.HTTP_202_ACCEPTED,
        )