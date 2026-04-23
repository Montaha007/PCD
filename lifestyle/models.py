# lifestyle/models.py
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from core.models import BaseModel


class LifestyleLog(BaseModel):
    """
    Per-day lifestyle entry. Field names match the Colab notebook's
    training DataFrame exactly so the trained lifestyle model can
    consume these rows without any renaming.

    Raw features (user-entered, 6):
        WorkoutTime, ReadingTime, PhoneTime, WorkHours,
        CaffeineIntake, RelaxationTime
    Derived features (computed on save, 2):
        Work_x_Caffeine       = WorkHours * CaffeineIntake
        Screen_Time_Intensity = PhoneTime / (RelaxationTime + 1)
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='lifestyle_logs'
    )
    date = models.DateField(help_text="The day this entry refers to.")

    # --- Raw inputs (ranges match training distribution) ---
    WorkoutTime = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(3)],
        help_text="Hours of workout today (0–3)."
    )
    ReadingTime = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(2)],
        help_text="Hours of reading today (0–2)."
    )
    PhoneTime = models.FloatField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Hours of phone use today (1–5)."
    )
    WorkHours = models.FloatField(
        validators=[MinValueValidator(4), MaxValueValidator(10)],
        help_text="Hours worked today (4–10)."
    )
    CaffeineIntake = models.PositiveIntegerField(
        validators=[MaxValueValidator(300)],
        help_text="Caffeine intake in mg (0–300)."
    )
    RelaxationTime = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(2)],
        help_text="Hours of relaxation today (0–2)."
    )

    # --- Derived (computed, not editable from API) ---
    Work_x_Caffeine = models.FloatField(editable=False)
    Screen_Time_Intensity = models.FloatField(editable=False)

    class Meta:
        unique_together = ('user', 'date')
        ordering = ['-date']
        indexes = [models.Index(fields=['user', '-date'])]

    def save(self, *args, **kwargs):
        """Single source of truth for derived features."""
        self.Work_x_Caffeine = self.WorkHours * self.CaffeineIntake
        self.Screen_Time_Intensity = self.PhoneTime / (self.RelaxationTime + 1)
        super().save(*args, **kwargs)

    def to_feature_dict(self):
        """
        Returns the dict the AI pipeline feeds to the lifestyle model.
        Key order matches the trained DataFrame — DO NOT reorder.
        """
        return {
            'WorkoutTime': self.WorkoutTime,
            'ReadingTime': self.ReadingTime,
            'PhoneTime': self.PhoneTime,
            'WorkHours': self.WorkHours,
            'CaffeineIntake': self.CaffeineIntake,
            'RelaxationTime': self.RelaxationTime,
            'Work_x_Caffeine': self.Work_x_Caffeine,
            'Screen_Time_Intensity': self.Screen_Time_Intensity,
        }

    def __str__(self):
        return f"Lifestyle({self.user_id}, {self.date})"