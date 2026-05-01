# ai/models.py
# ============================================================================
# DailyProgress — one row per (user, date). It tracks the progress bar at the
# top of the web UI and stores every output from the pipeline shown in
# image_1.png.
#
# Lifecycle:
#
#   user submits sleep log     ─► sleep_log FK set     ─► 25%
#   user submits lifestyle log ─► lifestyle_log FK set ─► 50%
#   user submits journal text  ─► journal_text set     ─► 75%
#                                  │
#                                  ▼  (pipeline auto-triggers)
#   3 ML models run in parallel  ─► model_outputs    ─► 80%
#   Agent 1 (Correlation)        ─► unified_profile  ─► 87%
#   Agent 2 (Reasoning)          ─► reasoning_report ─► 92%
#   Agent 3 (Recommendation)     ─► final_output     ─► 97%
#   COMPLETE                                          ─► 100%
# ============================================================================
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone

from core.models import BaseModel


class DailyProgress(BaseModel):
    """One row per (user, day). Drives the progress bar AND owns all
    pipeline outputs for that day."""

    class Status(models.TextChoices):
        WAITING        = "WAITING",        "Waiting for inputs"
        MODELS_RUNNING = "MODELS_RUNNING", "Models running"
        MODELS_DONE    = "MODELS_DONE",    "Models complete"
        AGENT1_DONE    = "AGENT1_DONE",    "Correlation agent done"
        AGENT2_DONE    = "AGENT2_DONE",    "Reasoning agent done"
        AGENT3_DONE    = "AGENT3_DONE",    "Recommendation agent done"
        COMPLETE       = "COMPLETE",       "Complete"
        FAILED         = "FAILED",         "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="daily_progress",
    )
    date = models.DateField(default=timezone.localdate)

    # ── Inputs (populated as the user submits each feature) ───────────────
    sleep_log = models.ForeignKey(
        "sleeplog.SleepLog",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="+",
    )
    lifestyle_log = models.ForeignKey(
        "lifestyle.LifestyleLog",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="+",
    )
    journal_text = models.TextField(blank=True, default="")

    # ── Per-stage outputs of the AI pipeline ──────────────────────────────
    model_outputs     = models.JSONField(null=True, blank=True)  # after step 1
    unified_profile   = models.JSONField(null=True, blank=True)  # after Agent 1
    reasoning_report  = models.JSONField(null=True, blank=True)  # after Agent 2
    final_output      = models.JSONField(null=True, blank=True)  # after Agent 3
    pipeline_metadata = models.JSONField(null=True, blank=True)

    # ── Lifecycle bookkeeping ─────────────────────────────────────────────
    status = models.CharField(
        max_length=24, choices=Status.choices, default=Status.WAITING,
    )
    error_message = models.TextField(blank=True, default="")
    started_at    = models.DateTimeField(null=True, blank=True)
    finished_at   = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("user", "date")
        ordering = ["-date", "-created_at"]
        indexes = [
            models.Index(fields=["user", "-date"]),
            models.Index(fields=["status"]),
        ]
        verbose_name = "Daily progress"
        verbose_name_plural = "Daily progress"

    def __str__(self) -> str:
        return f"DailyProgress(user={self.user_id}, date={self.date}, status={self.status})"

    # ── Submission flags — drive the progress bar ─────────────────────────
    @property
    def sleep_submitted(self) -> bool:
        return self.sleep_log_id is not None

    @property
    def lifestyle_submitted(self) -> bool:
        return self.lifestyle_log_id is not None

    @property
    def journal_submitted(self) -> bool:
        return bool(self.journal_text and self.journal_text.strip())

    @property
    def submitted_count(self) -> int:
        return sum([self.sleep_submitted, self.lifestyle_submitted, self.journal_submitted])

    @property
    def all_submitted(self) -> bool:
        return self.submitted_count == 3

    # ── Progress percent — single number for the front-end bar ────────────
    _STAGE_PERCENTS = {
        Status.MODELS_RUNNING: 78,
        Status.MODELS_DONE:    82,
        Status.AGENT1_DONE:    87,
        Status.AGENT2_DONE:    92,
        Status.AGENT3_DONE:    97,
        Status.COMPLETE:       100,
        Status.FAILED:         100,   # bar shows red rather than half-empty
    }

    @property
    def progress_percent(self) -> int:
        if self.status in self._STAGE_PERCENTS:
            return self._STAGE_PERCENTS[self.status]
        # WAITING — depends on how many features are in
        return self.submitted_count * 25

    # ── Pipeline-readiness flag ───────────────────────────────────────────
    @property
    def can_start_pipeline(self) -> bool:
        """True only when all 3 inputs are in AND pipeline hasn't started."""
        return self.all_submitted and self.status == self.Status.WAITING

    # ── Atomic field + status update used by the orchestrator ─────────────
    def mark(self, status: "DailyProgress.Status", **fields) -> None:
        self.status = status
        for key, val in fields.items():
            setattr(self, key, val)
        self.save(update_fields=["status", *fields.keys(), "updated_at"])

    @property
    def is_complete(self) -> bool:
        return self.status == self.Status.COMPLETE

    @property
    def is_failed(self) -> bool:
        return self.status == self.Status.FAILED
    