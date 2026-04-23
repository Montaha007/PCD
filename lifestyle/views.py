# lifestyle/views.py
import logging

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import LifestyleLog
from .serializers import LifestyleLogSerializer
from ai.services import predict_lifestyle

logger = logging.getLogger(__name__)


class LifestyleLogViewSet(viewsets.ModelViewSet):
    serializer_class = LifestyleLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return LifestyleLog.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        """
        Upsert behavior: if a log already exists for (user, date),
        update it instead of raising IntegrityError.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        date = serializer.validated_data['date']
        existing = LifestyleLog.objects.filter(
            user=request.user, date=date
        ).first()

        if existing:
            # Update the existing log with the new values
            update_serializer = self.get_serializer(
                existing, data=request.data, partial=False
            )
            update_serializer.is_valid(raise_exception=True)
            update_serializer.save()
            return Response(update_serializer.data, status=status.HTTP_200_OK)

        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"], url_path="predict")
    def predict(self, request, pk=None):
        """
        GET /api/lifestyle/logs/{id}/predict/
        Returns predicted sleep hours + quality label.
        """
        lifestyle_log = self.get_object()
        try:
            return Response(predict_lifestyle(lifestyle_log))
        except FileNotFoundError:
            logger.exception("Lifestyle model artifact missing")
            return Response(
                {"error": "Lifestyle model is not available."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except Exception:
            logger.exception("Lifestyle prediction failed for log %s", pk)
            return Response(
                {"error": "Prediction service failed."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )