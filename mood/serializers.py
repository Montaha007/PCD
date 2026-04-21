from rest_framework import serializers
from .models import JournalEntry


class JournalEntryCreateSerializer(serializers.ModelSerializer):
    """Used on POST — only accepts content from the client."""

    class Meta:
        model  = JournalEntry
        fields = ["content"]


class JournalEntrySerializer(serializers.ModelSerializer):
    """Used on GET — exposes all fields including AI results."""

    class Meta:
        model  = JournalEntry
        fields = [
            "id",
            "content",
            "predicted_mood",
            "analysis_text",
            "status",
            "created_at",
        ]
        read_only_fields = fields
