# audiotherapy/models.py
from django.db import models
from core.models import BaseModel


class Disorder(models.TextChoices):
    """Mental health states recognized by the NLP model."""
    NORMAL      = 'normal',      'Normal'
    ANXIETY     = 'anxiety',     'Anxiety'
    DEPRESSION  = 'depression',  'Depression'
    STRESS      = 'stress',      'Stress'
    BIPOLAR     = 'bipolar',     'Bipolar'
    SUICIDAL    = 'suicidal',    'Suicidal'
    PERSONALITY = 'personality', 'Personality Disorder'


class BrainwaveType(models.TextChoices):
    """Brainwave bands used in audio therapy."""
    DELTA = 'delta', 'Delta (0.5-4 Hz)'   # deep sleep
    THETA = 'theta', 'Theta (4-8 Hz)'     # meditation, REM
    ALPHA = 'alpha', 'Alpha (8-13 Hz)'    # relaxation
    BETA  = 'beta',  'Beta (13-30 Hz)'    # focus, alertness
    GAMMA = 'gamma', 'Gamma (30-100 Hz)'  # cognition


class DisorderRecommendation(BaseModel):
    """
    Maps a disorder → brainwave band with a priority score.
    The actual sound is generated client-side via Tone.js.
    """
    disorder  = models.CharField(max_length=20, choices=Disorder.choices)
    brainwave = models.CharField(max_length=10, choices=BrainwaveType.choices)
    priority  = models.PositiveIntegerField(
        default=1,
        help_text="Lower = higher priority (1 = primary)"
    )
    # Specific Hz to target inside the band (e.g., 10 Hz for relaxation alpha)
    target_frequency_hz = models.FloatField(
        help_text="Specific frequency to generate (within the brainwave band)"
    )
    # Carrier frequency for binaural beats (typically 100-300 Hz)
    carrier_frequency_hz = models.FloatField(
        default=200.0,
        help_text="Base carrier tone for binaural beats"
    )
    rationale = models.TextField(
        blank=True,
        help_text="Why this brainwave is recommended (shown to user)"
    )

    class Meta:
        unique_together = ('disorder', 'brainwave')
        ordering = ['disorder', 'priority']

    def __str__(self):
        return f"{self.get_disorder_display()} → {self.get_brainwave_display()} @ {self.target_frequency_hz}Hz"