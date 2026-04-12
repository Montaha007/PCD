from rest_framework import serializers
from .models import SleepLog


class SleepLogSerializer(serializers.ModelSerializer):
    # Computed on the model — never writable from the API
    calculated_sleep_duration = serializers.DurationField(read_only=True)
    # Snapshotted from user profile — never writable from the API
    duration_of_problems = serializers.IntegerField(read_only=True)
    # User is injected by the view, not supplied by the client
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = SleepLog
        fields = [
            'id',
            'user',
            'sleep_time',
            'wake_up_time',
            'calculated_sleep_duration',
            'satisfaction_of_sleep',
            'late_night_sleep',
            'wake_up_frequently',
            'sleep_at_daytime',
            'drowsiness_tiredness',
            'recent_psychological_attack',
            'afraid_of_sleeping',
            'duration_of_problems',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']
