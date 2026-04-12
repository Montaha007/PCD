from django.db import models
from django.conf import settings


class SleepLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sleep_logs',
    )
    sleep_time = models.DateTimeField()
    wake_up_time = models.DateTimeField()
    calculated_sleep_duration = models.DurationField(editable=False)

    satisfaction_of_sleep = models.BooleanField()
    late_night_sleep = models.BooleanField(default=False)
    wake_up_frequently = models.BooleanField(default=False)
    sleep_at_daytime = models.BooleanField(default=False)
    drowsiness_tiredness = models.BooleanField(default=False)
    recent_psychological_attack = models.BooleanField(default=False)
    afraid_of_sleeping = models.BooleanField(default=False)

    # Snapshot from user.insomnia_duration_years at creation time — not editable
    duration_of_problems = models.PositiveSmallIntegerField(editable=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        # Auto-calculate duration from the two timestamps
        self.calculated_sleep_duration = self.wake_up_time - self.sleep_time
        # Snapshot the user's insomnia duration only on first save
        if not self.pk:
            self.duration_of_problems = self.user.insomnia_duration_years
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.email} — {self.sleep_time.date()}"
