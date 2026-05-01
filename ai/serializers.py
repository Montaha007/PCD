# ai/serializers.py
# ============================================================================
# DailyProgressSerializer — the response the progress bar polls.
#
# Heavy JSON payloads (model_outputs, unified_profile, reasoning_report) are
# only returned once the pipeline finishes — keeps poll responses small.
# ============================================================================
from rest_framework import serializers

from ai.models import DailyProgress


class JournalSubmissionSerializer(serializers.Serializer):
    text = serializers.CharField(allow_blank=False, max_length=10_000)


class DailyProgressSerializer(serializers.ModelSerializer):
    progress_percent    = serializers.IntegerField(read_only=True)
    sleep_submitted     = serializers.BooleanField(read_only=True)
    lifestyle_submitted = serializers.BooleanField(read_only=True)
    journal_submitted   = serializers.BooleanField(read_only=True)
    submitted_count     = serializers.IntegerField(read_only=True)
    all_submitted       = serializers.BooleanField(read_only=True)
    current_step     = serializers.IntegerField(read_only=True)
    total_steps      = serializers.IntegerField(read_only=True)

    final_output     = serializers.SerializerMethodField()
    reasoning_report = serializers.SerializerMethodField()
    unified_profile  = serializers.SerializerMethodField()

    class Meta:
        model  = DailyProgress
        fields = (
            "id", "date", "status",
            "progress_percent", "current_step", "total_steps",
            "sleep_submitted", "lifestyle_submitted", "journal_submitted",
            "submitted_count", "all_submitted",
            "started_at", "finished_at",
            "pipeline_metadata",
            "unified_profile", "reasoning_report", "final_output",
            "error_message",
        )
        read_only_fields = fields

    def _only_when_complete(self, obj, attr):
        return getattr(obj, attr) if obj.is_complete else None

    def get_final_output(self, obj):
        return self._only_when_complete(obj, "final_output")

    def get_reasoning_report(self, obj):
        return self._only_when_complete(obj, "reasoning_report")

    def get_unified_profile(self, obj):
        return self._only_when_complete(obj, "unified_profile")
    
    