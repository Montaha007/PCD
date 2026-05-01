# ai/progress.py
# ============================================================================
# Service helpers that the sleep / lifestyle / journal endpoints call after
# they save the user's input. Each helper:
#
#   1. Gets-or-creates the user's DailyProgress row for today.
#   2. Sets the appropriate FK / text field.
#   3. If all 3 features are now in AND the pipeline hasn't started yet,
#      enqueues the pipeline thread.
#
# select_for_update + status check make this idempotent.
# ============================================================================
from __future__ import annotations

import logging
from datetime import date as date_cls
from typing import Optional

from django.db import transaction
from django.utils import timezone

from ai.models import DailyProgress
from ai.runner import submit_pipeline

logger = logging.getLogger(__name__)


def _record(user, *, day: Optional[date_cls], **field_updates) -> DailyProgress:
    day = day or timezone.localdate()

    with transaction.atomic():
        # Locks the row so two concurrent submissions can't both
        # think they're the trigger.
        progress, _ = (
            DailyProgress.objects
            .select_for_update()
            .get_or_create(user=user, date=day)
        )

        for field, value in field_updates.items():
            setattr(progress, field, value)
        progress.save(update_fields=[*field_updates.keys(), "updated_at"])

        # If this submission completes the trio, kick off the pipeline.
        if progress.can_start_pipeline:
            logger.info(
                "All inputs in for user=%s day=%s — enqueueing pipeline",
                user.id, day,
            )
            submit_pipeline(progress.id)

    return progress


# ── Public API: one helper per feature ─────────────────────────────────────
def record_sleep(user, sleep_log, *, day: Optional[date_cls] = None) -> DailyProgress:
    """Call this from your SleepLog create/update view after .save()."""
    return _record(user, day=day or sleep_log.date, sleep_log=sleep_log)


def record_lifestyle(user, lifestyle_log, *, day: Optional[date_cls] = None) -> DailyProgress:
    """Call this from your LifestyleLog create/update view after .save()."""
    return _record(user, day=day or lifestyle_log.date, lifestyle_log=lifestyle_log)


def record_journal(user, text: str, *, day: Optional[date_cls] = None) -> DailyProgress:
    """Call this from your Journal endpoint after the user submits the text."""
    return _record(user, day=day, journal_text=text or "")


# ── Read helper ────────────────────────────────────────────────────────────
def get_today_progress(user, *, day: Optional[date_cls] = None) -> Optional[DailyProgress]:
    """Returns the user's DailyProgress for *day* (default: today), or None."""
    day = day or timezone.localdate()
    return (
        DailyProgress.objects
        .filter(user=user, date=day)
        .first()
    )


# ── Manual rerun ───────────────────────────────────────────────────────────
def request_rerun(progress: DailyProgress) -> DailyProgress:
    """
    Reset the pipeline outputs and re-enqueue. Only allowed on COMPLETE or
    FAILED rows — refusing mid-pipeline reruns avoids stomping on a thread
    that's still writing.
    """
    if progress.status not in (DailyProgress.Status.COMPLETE, DailyProgress.Status.FAILED):
        raise ValueError(
            f"Can't rerun a pipeline in status={progress.status}. "
            "Wait for it to finish first."
        )
    if not progress.all_submitted:
        raise ValueError("Can't rerun without all 3 inputs submitted.")

    with transaction.atomic():
        progress.status            = DailyProgress.Status.WAITING
        progress.error_message     = ""
        progress.model_outputs     = None
        progress.unified_profile   = None
        progress.reasoning_report  = None
        progress.final_output      = None
        progress.pipeline_metadata = None
        progress.started_at        = None
        progress.finished_at       = None
        progress.save()

        submit_pipeline(progress.id)

    return progress