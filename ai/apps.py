# ai/apps.py
from django.apps import AppConfig


class AiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ai"

    def ready(self):
        # Register the post_save handlers for SleepLog and LifestyleLog.
        # If you'd rather wire submissions manually from the views, comment
        # out the next line.
        from ai import signals  # noqa: F401