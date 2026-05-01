# ai/orchestrator.py
# ============================================================================
# SleepAnalysisOrchestrator
# -------------------------
# Runs the pipeline shown in image_1.png against a single DailyProgress row:
#
#     [3 ML models in parallel]  →  Agent 1  →  Agent 2  →  Agent 3  →  persist
#
# CrewAI agent execution is delegated to crew.run_pipeline, which already
# exists in your project.
# ============================================================================
from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Any

from django.db import transaction
from django.utils import timezone as djtz

from ai.models import DailyProgress

# Existing services in your project
from ai.services import predict_sleep, predict_lifestyle
from ai.services import analyze_journal  # rename if your NLP entry point differs

# Existing CrewAI orchestration from crew.py
from crew import run_pipeline


logger = logging.getLogger(__name__)


class PipelineError(Exception):
    """Wraps any per-stage failure with a stage tag for cleaner error messages."""

    def __init__(self, stage: str, original: Exception):
        self.stage    = stage
        self.original = original
        super().__init__(f"[{stage}] {original.__class__.__name__}: {original}")


class SleepAnalysisOrchestrator:
    """
    One instance per DailyProgress row.

        orch = SleepAnalysisOrchestrator(progress)
        orch.execute()                      # runs the whole pipeline

        # OR step-by-step (debugging / partial retries from a shell):
        orch.step_run_models()
        orch.step_correlation_agent()
        orch.step_reasoning_agent()
        orch.step_recommendation_agent()
        orch.step_persist_report()
    """

    def __init__(self, progress: DailyProgress):
        self.progress = progress
        # CrewAI executes the 3 agents inside one kickoff() call, so we run it
        # once during step_correlation_agent and unpack the result in steps 3-4.
        self._pipeline_cache: dict | None = None
        self._stage_timings: dict[str, float] = {}

    # ─────────────────────────────────────────────────────────────────────
    def execute(self) -> DailyProgress:
        self.progress.mark(
            DailyProgress.Status.MODELS_RUNNING,
            started_at=djtz.now(),
        )
        try:
            self.step_run_models()
            self.step_correlation_agent()
            self.step_reasoning_agent()
            self.step_recommendation_agent()
            self.step_persist_report()
        except PipelineError as exc:
            logger.exception(
                "Pipeline failed at stage=%s progress_id=%s",
                exc.stage, self.progress.id,
            )
            self.progress.mark(
                DailyProgress.Status.FAILED,
                error_message=f"[{exc.stage}] {exc.original}",
                finished_at=djtz.now(),
            )
            raise
        return self.progress

    # ── STEP 1 — Models → Agent 1 input ──────────────────────────────────
    def step_run_models(self) -> dict:
        t0 = time.perf_counter()
        try:
            results: dict[str, Any] = {}

            # I/O-bound (Qdrant, Neo4j, Groq) → threads give clean ~3x speedup.
            with ThreadPoolExecutor(max_workers=3) as pool:
                futures = {
                    pool.submit(predict_sleep, self.progress.sleep_log):
                        "sleep_model",
                    pool.submit(predict_lifestyle, self.progress.lifestyle_log):
                        "lifestyle_model",
                    pool.submit(analyze_journal, self.progress.journal_text):
                        "nlp_mental_health_model",
                }
                for future in as_completed(futures):
                    key = futures[future]
                    results[key] = future.result()  # re-raises on failure

            envelope = {
                "user_id":   str(self.progress.user_id),
                "run_id":    str(self.progress.id),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                **results,
            }

            self._stage_timings["models"] = round(time.perf_counter() - t0, 2)
            self.progress.mark(
                DailyProgress.Status.MODELS_DONE,
                model_outputs=envelope,
            )
            logger.info(
                "[progress=%s] Models complete (%.2fs)",
                self.progress.id, self._stage_timings["models"],
            )
            return envelope

        except Exception as exc:
            raise PipelineError("MODELS", exc) from exc

    # ── STEP 2 — Agent 1: Correlation ────────────────────────────────────
    def step_correlation_agent(self) -> dict:
        if self.progress.model_outputs is None:
            raise PipelineError(
                "AGENT_1_CORRELATION",
                RuntimeError("step_run_models() must be called first"),
            )

        t0 = time.perf_counter()
        try:
            # Single CrewAI invocation — runs Agent 1 → Agent 2 → Agent 3
            # sequentially with automatic context injection between tasks.
            self._pipeline_cache = run_pipeline(self.progress.model_outputs)

            unified_profile = self._pipeline_cache["unified_profile"]
            self._stage_timings["agents_total"] = round(time.perf_counter() - t0, 2)

            self.progress.mark(
                DailyProgress.Status.AGENT1_DONE,
                unified_profile=unified_profile,
            )
            logger.info(
                "[progress=%s] Agent 1 done (insomnia=%s, tier=%s)",
                self.progress.id,
                unified_profile.get("insomnia_detected"),
                unified_profile.get("confidence_tier"),
            )
            return unified_profile

        except Exception as exc:
            raise PipelineError("AGENT_1_CORRELATION", exc) from exc

    # ── STEP 3 — Agent 2: Reasoning ──────────────────────────────────────
    def step_reasoning_agent(self) -> dict:
        if self._pipeline_cache is None:
            raise PipelineError(
                "AGENT_2_REASONING",
                RuntimeError("step_correlation_agent() must be called first"),
            )

        try:
            report = self._pipeline_cache["reasoning_report"]
            self.progress.mark(
                DailyProgress.Status.AGENT2_DONE,
                reasoning_report=report,
            )
            logger.info(
                "[progress=%s] Agent 2 done (confirmed=%s, causes=%d)",
                self.progress.id,
                report.get("insomnia_confirmed"),
                len(report.get("root_causes", []) or []),
            )
            return report

        except Exception as exc:
            raise PipelineError("AGENT_2_REASONING", exc) from exc

    # ── STEP 4 — Agent 3: Recommendation ─────────────────────────────────
    def step_recommendation_agent(self) -> dict:
        if self._pipeline_cache is None:
            raise PipelineError(
                "AGENT_3_RECOMMENDATION",
                RuntimeError("step_correlation_agent() must be called first"),
            )

        try:
            final = self._pipeline_cache["final_output"]
            self.progress.mark(
                DailyProgress.Status.AGENT3_DONE,
                final_output=final,
            )
            logger.info(
                "[progress=%s] Agent 3 done (referral=%s)",
                self.progress.id,
                final.get("referral_required"),
            )
            return final

        except Exception as exc:
            raise PipelineError("AGENT_3_RECOMMENDATION", exc) from exc

    # ── STEP 5 — Persist final report ────────────────────────────────────
    @transaction.atomic
    def step_persist_report(self) -> DailyProgress:
        profile = self.progress.unified_profile  or {}
        report  = self.progress.reasoning_report or {}
        final   = self.progress.final_output     or {}

        metadata = {
            "framework":          "CrewAI",
            "process":            "sequential-django-orchestrated",
            "agents":             3,
            "tasks":              3,
            "stage_timings":      self._stage_timings,
            "confidence_tier":    profile.get("confidence_tier"),
            "overall_confidence": profile.get("overall_confidence"),
            "insomnia_detected":  profile.get("insomnia_detected"),
            "insomnia_confirmed": report.get("insomnia_confirmed"),
            "referral_required":  final.get("referral_required"),
            "root_cause_count":   len(report.get("root_causes", []) or []),
            "completed_at":       djtz.now().isoformat(),
        }

        self.progress.mark(
            DailyProgress.Status.COMPLETE,
            pipeline_metadata=metadata,
            finished_at=djtz.now(),
        )
        logger.info("[progress=%s] Pipeline COMPLETE", self.progress.id)
        return self.progress