# ai/runner.py
# ============================================================================
# In-process background runner — the Celery-free alternative.
#
# Uses a single module-level ThreadPoolExecutor to run the pipeline in a
# background thread within the Django process.
#
# Why this works for an MVP
# -------------------------
#   • No external broker (no Redis), no extra service to deploy.
#   • Bounded concurrency (max_workers=2) prevents thundering CPU.
#   • transaction.on_commit() ensures the thread starts AFTER the DB write
#     of the final input commits — no race where the worker reads stale data.
#
# Production caveats
# ------------------
#   • Tasks live in the Django worker process. If gunicorn restarts that
#     worker, in-flight pipelines are lost — the row stays in
#     MODELS_RUNNING / AGENT*_DONE forever.
#   • Use gunicorn with `--worker-class gthread` (or threads ≥ 4 on the sync
#     worker) so the request thread isn't blocked by the background thread.
#   • When you outgrow this, swap _PIPELINE_EXECUTOR.submit for celery's
#     run_sleep_analysis_pipeline.delay — the contract is identical.
# ============================================================================
from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor

from django.db import close_old_connections, transaction

logger = logging.getLogger(__name__)


# ── Module-level singleton ──────────────────────────────────────────────────
_PIPELINE_EXECUTOR = ThreadPoolExecutor(
    max_workers=2,
    thread_name_prefix="ai-pipeline",
)


# ── Internals ───────────────────────────────────────────────────────────────
def _run_pipeline(progress_id: str) -> None:
    """Body of the background thread."""
    from ai.models import DailyProgress
    from ai.orchestrator import SleepAnalysisOrchestrator, PipelineError

    # Each thread needs a fresh DB connection.
    close_old_connections()

    try:
        progress = DailyProgress.objects.select_related(
            "user", "sleep_log", "lifestyle_log",
        ).get(pk=progress_id)
    except DailyProgress.DoesNotExist:
        logger.error("DailyProgress %s vanished before worker picked it up", progress_id)
        return

    try:
        SleepAnalysisOrchestrator(progress).execute()
    except PipelineError:
        # Already logged + persisted to the row by the orchestrator.
        pass
    except Exception:
        logger.exception("Unexpected error in pipeline thread for %s", progress_id)
    finally:
        close_old_connections()


# ── Public API ──────────────────────────────────────────────────────────────
def submit_pipeline(progress_id: str) -> None:
    """
    Schedule the pipeline to run in a background thread, but ONLY after the
    current DB transaction commits. Prevents races where the worker starts
    before the journal_text update is visible.
    """
    progress_id = str(progress_id)

    def _enqueue():
        future = _PIPELINE_EXECUTOR.submit(_run_pipeline, progress_id)
        future.add_done_callback(_log_thread_exception)
        logger.info("Enqueued pipeline for progress=%s", progress_id)

    transaction.on_commit(_enqueue)


def _log_thread_exception(future):
    exc = future.exception()
    if exc is not None:
        logger.error("Pipeline thread raised: %r", exc)


# ── Synchronous run (tests + manual trigger) ───────────────────────────────
def run_pipeline_sync(progress_id: str) -> None:
    """Run the pipeline inline. Useful for tests or `manage.py shell`."""
    _run_pipeline(str(progress_id))