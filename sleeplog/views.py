import traceback

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from django.conf import settings
from django.utils import timezone

from .models import SleepLog, DailyWellnessAnalysis
from .serializers import SleepLogSerializer
from ai.services import predict_sleep
from ai.agents.orchestrator import get_agent


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

    @action(detail=True, methods=["get", "post"], url_path="wellness-analysis")
    def wellness_analysis(self, request, pk=None):
        """
        GET/POST /api/sleeplog/{id}/wellness-analysis/

        Runs the full Numa three-agent pipeline and returns personalized
        diagnosis, root causes, and an action plan.
        """
        sleep_log = self.get_object()
        try:
            today = timezone.localdate()
            force = request.query_params.get("force") == "1"

            snapshot = DailyWellnessAnalysis.objects.filter(
                user=request.user,
                analysis_date=today,
            ).first()

            if request.method == "GET":
                if snapshot:
                    return Response(
                        {
                            "success": True,
                            "data": snapshot.result,
                            "cached": True,
                            "analysis_date": str(snapshot.analysis_date),
                        }
                    )
                return Response(
                    {"success": False, "error": "No analysis saved for today."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            if snapshot and not force:
                return Response(
                    {
                        "success": True,
                        "data": snapshot.result,
                        "cached": True,
                        "analysis_date": str(snapshot.analysis_date),
                    }
                )

            duration_hours = sleep_log.calculated_sleep_duration.total_seconds() / 3600
            user_data = {
                "user_id": str(sleep_log.user.id),
                "sleep_features": {
                    # Canonical 9 features (must match ai/models/sleep_feature_columns.json)
                    "Total_sleep_time(hour)": duration_hours,
                    "Satisfaction_of_sleep": int(sleep_log.satisfaction_of_sleep),
                    "Late_night_sleep": int(sleep_log.late_night_sleep),
                    "Wakeup_frequently_during_sleep": int(sleep_log.wake_up_frequently),
                    "Sleep_at_daytime": int(sleep_log.sleep_at_daytime),
                    "Drowsiness_tiredness": int(sleep_log.drowsiness_tiredness),
                    "Duration_of_this_problems(years)": int(sleep_log.duration_of_problems),
                    "Recent_psychological_attack": int(sleep_log.recent_psychological_attack),
                    "Afraid_of_getting_asleep": int(sleep_log.afraid_of_sleeping),
                },
                "lifestyle_features": {
                    "WorkoutTime": 0.5,
                    "ReadingTime": 0.3,
                    "PhoneTime": 4.2,
                    "WorkHours": 8.0,
                    "CaffeineIntake": 200,
                    "RelaxationTime": 1.0,
                },
                "journal_text": "",
            }

            agent = get_agent("wellness")
            result = agent.run(user_data)

            if result.get("success"):
                data = result["data"]
                final_output = data.get("final_output", {}) if isinstance(data, dict) else {}
                summary = final_output.get("plan_summary") or final_output.get("summary")

                DailyWellnessAnalysis.objects.update_or_create(
                    user=request.user,
                    analysis_date=today,
                    defaults={
                        "result": data,
                        "summary": summary,
                        "sleep_log": sleep_log,
                    },
                )

                return Response(
                    {
                        "success": True,
                        "data": data,
                        "cached": False,
                        "analysis_date": str(today),
                    }
                )
            return Response(
                {"success": False, "error": result.get("error", "Unknown error")},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as exc:
            detail = traceback.format_exc() if settings.DEBUG else str(exc)
            return Response(
                {"success": False, "error": str(exc), "detail": detail},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
