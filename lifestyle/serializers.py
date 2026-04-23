# lifestyle/serializers.py
from datetime import date as date_type
from rest_framework import serializers
from .models import LifestyleLog


class LifestyleLogSerializer(serializers.ModelSerializer):
    """
    Only the 6 raw features are writable.
    Derived features are read-only — the client cannot spoof them.
    """

    class Meta:
        model = LifestyleLog
        fields = [
            'id',
            'date',
            # Writable
            'WorkoutTime',
            'ReadingTime',
            'PhoneTime',
            'WorkHours',
            'CaffeineIntake',
            'RelaxationTime',
            # Read-only derived (returned in response for dashboards)
            'Work_x_Caffeine',
            'Screen_Time_Intensity',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'Work_x_Caffeine',
            'Screen_Time_Intensity',
            'created_at',
            'updated_at',
        ]

    def validate_date(self, value):
        """Prevent future-dated entries."""
        if value > date_type.today():
            raise serializers.ValidationError(
                "Cannot log lifestyle data for a future date."
            )
        return value