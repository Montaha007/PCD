import traceback

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from django.conf import settings

from .models import SleepLog
from .serializers import SleepLogSerializer
from ai.services import predict_sleep


class SleepLogViewSet(viewsets.ModelViewSet):
    serializer_class = SleepLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SleepLog.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["get"], url_path="predict")
    def predict(self, request, pk=None):
        """
        GET /api/sleeplog/{id}/predict/

        Runs the AI pipeline on the requested log and returns:
        - disorder prediction from Qdrant majority label (0/1), and
        - score from the ML model probability.
        """
        sleep_log = self.get_object()
        try:
            result = predict_sleep(sleep_log)
            return Response(result)
        except Exception as exc:
            # Only expose details in DEBUG mode
            detail = traceback.format_exc() if settings.DEBUG else str(exc)
            return Response({"error": str(exc), "detail": detail},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
