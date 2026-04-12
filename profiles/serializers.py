from rest_framework import serializers

from .models import Profile


class ProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)
    full_name = serializers.CharField(source="user.full_name")
    age = serializers.IntegerField(source="user.age")
    gender = serializers.CharField(source="user.gender")
    country = serializers.CharField(source="user.country")
    notifications_enabled = serializers.BooleanField(source="user.notifications_enabled")

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
        ]

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
