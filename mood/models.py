from django.db import models
from django.conf import settings


class JournalEntry(models.Model):

    class Status(models.TextChoices):
        PENDING    = "PENDING",    "Pending"
        PROCESSING = "PROCESSING", "Processing"
        COMPLETED  = "COMPLETED",  "Completed"
        FAILED     = "FAILED",     "Failed"

    user    = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="journal_entries")
    content = models.TextField()

    # AI-populated fields (null until pipeline runs)
    predicted_mood = models.CharField(max_length=100, null=True, blank=True)
    analysis_text  = models.TextField(null=True, blank=True)
    status         = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"JournalEntry(user={self.user_id}, status={self.status}, created={self.created_at:%Y-%m-%d})"
