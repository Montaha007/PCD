from rest_framework import serializers

from .models import Profile


SETUP_STEP_KEYS = ["profile", "sleep", "lifestyle", "journal"]


class ProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)
    full_name = serializers.CharField(source="user.full_name")
    age = serializers.IntegerField(source="user.age")
    gender = serializers.CharField(source="user.gender")
    country = serializers.CharField(source="user.country")
    notifications_enabled = serializers.BooleanField(source="user.notifications_enabled")
    setup_completed_steps = serializers.SerializerMethodField()
    setup_completed_count = serializers.SerializerMethodField()
    setup_total_steps = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = [
            "email",
            "full_name",
            "age",
            "gender",
            "country",
            "timezone",
            "language",
            "notifications_enabled",
            "setup_completed_steps",
            "setup_completed_count",
            "setup_total_steps",
        ]

    def _get_setup_completed_steps(self, instance):
        cached = getattr(instance, "_setup_completed_steps_cache", None)
        if cached is not None:
            return cached

        from mood.models import JournalEntry
        from sleeplog.models import SleepLog
        from lifestyle.models import LifestyleLog

        user = instance.user
        completed = []

        # Registration + profile data exist and are considered setup complete.
        if all([user.full_name, user.age, user.gender, user.country, user.email]):
            completed.append("profile")

        if SleepLog.objects.filter(user=user).exists():
            completed.append("sleep")

        if LifestyleLog.objects.filter(user=user).exists():
            completed.append("lifestyle")

        prediction_statuses = [
            JournalEntry.Status.COMPLETED,
            JournalEntry.Status.NORMAL,
            JournalEntry.Status.ANXIETY,
            JournalEntry.Status.DEPRESSION,
            JournalEntry.Status.STRESS,
            JournalEntry.Status.BIPOLAR,
            JournalEntry.Status.SUICIDAL,
            JournalEntry.Status.PERSONALITY_DISORDER,
        ]
        has_journal_prediction = JournalEntry.objects.filter(
            user=user,
            status__in=prediction_statuses,
        ).exclude(predicted_mood__isnull=True).exclude(predicted_mood__exact="").exists()
        if has_journal_prediction:
            completed.append("journal")

        setattr(instance, "_setup_completed_steps_cache", completed)
        return completed

    def get_setup_completed_steps(self, instance):
        return self._get_setup_completed_steps(instance)

    def get_setup_completed_count(self, instance):
        return len(self._get_setup_completed_steps(instance))

    def get_setup_total_steps(self, _instance):
        return len(SETUP_STEP_KEYS)

    def update(self, instance, validated_data):
        user_data = validated_data.pop("user", {})

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if user_data:
            for attr, value in user_data.items():
                setattr(instance.user, attr, value)
            instance.user.save(update_fields=list(user_data.keys()))

        return instance
