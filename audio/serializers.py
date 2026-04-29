# audiotherapy/serializers.py
from rest_framework import serializers


class RecommendationSerializer(serializers.Serializer):
    disorder              = serializers.CharField()
    disorder_display      = serializers.CharField()
    primary_brainwave     = serializers.CharField()
    primary_brainwave_display = serializers.CharField()
    target_frequency_hz   = serializers.FloatField()
    carrier_frequency_hz  = serializers.FloatField()
    rationale             = serializers.CharField()
    alternatives          = serializers.ListField()