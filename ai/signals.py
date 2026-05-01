# ai/signals.py
# ============================================================================
# Auto-wires SleepLog and LifestyleLog post_save into DailyProgress.
#
# OPTIONAL — if you'd rather call ai.progress.record_* explicitly from your
# views, comment out the signals import in apps.py.
#
# Signals are NOT used for the journal because there's no Journal model in
# the project. The journal endpoint calls record_journal() directly.
# ============================================================================
from __future__ import annotations

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from ai.progress import record_sleep, record_lifestyle

logger = logging.getLogger(__name__)


@receiver(post_save, sender="sleeplog.SleepLog")
def _on_sleep_log_saved(sender, instance, created, **kwargs):
    """Mirror the saved SleepLog onto DailyProgress for the same date."""
    try:
        record_sleep(instance.user, instance, day=instance.date)
    except Exception:
        logger.exception("Failed to record sleep submission for %s", instance)


@receiver(post_save, sender="lifestyle.LifestyleLog")
def _on_lifestyle_log_saved(sender, instance, created, **kwargs):
    """Mirror the saved LifestyleLog onto DailyProgress for the same date."""
    try:
        record_lifestyle(instance.user, instance, day=instance.date)
    except Exception:
        logger.exception("Failed to record lifestyle submission for %s", instance)