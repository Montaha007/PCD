from rest_framework import viewsets, permissions
from .models import SleepLog
from .serializers import SleepLogSerializer


class SleepLogViewSet(viewsets.ModelViewSet):
    serializer_class = SleepLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Users can only see their own logs
        return SleepLog.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Inject the authenticated user — the model.save() handles
        # calculated_sleep_duration and duration_of_problems automatically
        serializer.save(user=self.request.user)
