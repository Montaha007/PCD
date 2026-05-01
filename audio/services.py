# audio/services.py
# ============================================================================
# Bridge between the AI pipeline output and the audio therapy app.
#
# Agent 3 produces a final report whose `diagnosis` block names the user's
# dominant mental state. This module:
#   1. Pulls the user's most recent COMPLETE DailyProgress
#   2. Extracts the disorder label (with several fallback paths)
#   3. Normalises LLM phrasing variations ("anxious" → "anxiety")
#   4. Returns the matching DisorderRecommendation row (priority=1) +
#      any alternatives
# ============================================================================
from __future__ import annotations

import logging
from dataclasses import dataclass, asdict
from typing import Optional

from ai.models import DailyProgress
from audio.models import Disorder, DisorderRecommendation

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Synonym table — what Agent 3 / the NLP model might emit  →  Disorder enum.
# ─────────────────────────────────────────────────────────────────────────────
# The LLM doesn't always echo the rigid enum value, so we normalise here.
# Add more entries if you see new phrasings in production logs.
_SYNONYMS = {
    # anxiety family
    "anxiety":             Disorder.ANXIETY,
    "anxious":             Disorder.ANXIETY,
    "generalized anxiety": Disorder.ANXIETY,
    "gad":                 Disorder.ANXIETY,
    "panic":               Disorder.ANXIETY,

    # depression family
    "depression":  Disorder.DEPRESSION,
    "depressive":  Disorder.DEPRESSION,
    "low mood":    Disorder.DEPRESSION,
    "mdd":         Disorder.DEPRESSION,

    # stress family
    "stress":       Disorder.STRESS,
    "acute stress": Disorder.STRESS,
    "burnout":      Disorder.STRESS,

    # bipolar
    "bipolar":          Disorder.BIPOLAR,
    "bipolar disorder": Disorder.BIPOLAR,
    "mania":            Disorder.BIPOLAR,
    "manic":            Disorder.BIPOLAR,

    # suicidal ideation
    "suicidal":          Disorder.SUICIDAL,
    "suicidal ideation": Disorder.SUICIDAL,
    "self-harm":         Disorder.SUICIDAL,
    "self harm":         Disorder.SUICIDAL,

    # personality
    "personality":          Disorder.PERSONALITY,
    "personality disorder": Disorder.PERSONALITY,
    "borderline":           Disorder.PERSONALITY,
    "bpd":                  Disorder.PERSONALITY,

    # baseline
    "normal":      Disorder.NORMAL,
    "healthy":     Disorder.NORMAL,
    "no_insomnia": Disorder.NORMAL,
    "none":        Disorder.NORMAL,
}


# ─────────────────────────────────────────────────────────────────────────────
# Public dataclass returned to the view
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class AudioRecommendation:
    """The shape returned to the frontend audio page."""
    # Provenance — which pipeline run produced this, and from which stage
    source_progress_id: Optional[str]
    source_stage:       str           # "agent_3" | "agent_1" | "model_layer" | "fallback"

    # Disorder identity
    disorder:         str
    disorder_display: str

    # Primary track — what the audio player should auto-load
    primary_brainwave:         str
    primary_brainwave_display: str
    target_frequency_hz:       float
    carrier_frequency_hz:      float
    rationale:                 str

    # Alternatives (priority 2+) — for an "Other tracks" UI section
    alternatives: list

    # Pipeline context — lets the UI show a "based on your latest analysis…" line
    diagnosis_summary: Optional[str] = None
    confidence_tier:   Optional[str] = None
    referral_required: Optional[bool] = None

    def to_dict(self) -> dict:
        return asdict(self)


# ─────────────────────────────────────────────────────────────────────────────
# Public service entry point
# ─────────────────────────────────────────────────────────────────────────────
def recommend_audio_for_user(user) -> AudioRecommendation:
    """
    Return an AudioRecommendation tailored to the user's latest pipeline run.
    Falls back to Disorder.NORMAL if nothing usable is found.
    """
    progress = (
        DailyProgress.objects
        .filter(user=user, status=DailyProgress.Status.COMPLETE)
        .order_by("-date", "-created_at")
        .first()
    )

    disorder, source_stage = _resolve_disorder(progress)
    primary, alternatives = _load_recommendations(disorder)

    profile = (progress.unified_profile if progress else None) or {}
    final   = (progress.final_output    if progress else None) or {}

    return AudioRecommendation(
        source_progress_id= str(progress.id) if progress else None,
        source_stage=       source_stage,

        disorder=           disorder,
        disorder_display=   dict(Disorder.choices)[disorder],

        primary_brainwave=         primary.brainwave,
        primary_brainwave_display= primary.get_brainwave_display(),
        target_frequency_hz=       primary.target_frequency_hz,
        carrier_frequency_hz=      primary.carrier_frequency_hz,
        rationale=                 primary.rationale or "Recommended for your current state.",

        alternatives=[
            {
                "brainwave":            r.brainwave,
                "brainwave_display":    r.get_brainwave_display(),
                "target_frequency_hz":  r.target_frequency_hz,
                "carrier_frequency_hz": r.carrier_frequency_hz,
                "rationale":            r.rationale,
            }
            for r in alternatives
        ],

        diagnosis_summary= _extract_summary(final),
        confidence_tier=   profile.get("confidence_tier"),
        referral_required= final.get("referral_required"),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Resolution logic
# ─────────────────────────────────────────────────────────────────────────────
def _resolve_disorder(progress: Optional[DailyProgress]) -> tuple[str, str]:
    """
    Walk the priority list of locations Agent 3 / Agent 1 / the NLP model
    could have stored the dominant mental state. Return (disorder_value, source).
    """
    if progress is None:
        logger.info("No completed DailyProgress for user — using NORMAL fallback")
        return Disorder.NORMAL, "fallback"

    final   = progress.final_output    or {}
    profile = progress.unified_profile or {}

    # 1) Agent 3 — final_output.diagnosis.dominant_mental_state
    raw = (
        _safe_get(final, "diagnosis", "dominant_mental_state")
        or _safe_get(final, "diagnosis", "primary_disorder")
        or _safe_get(final, "diagnosis", "label")
    )
    if raw and (mapped := _normalise(raw)):
        return mapped, "agent_3"

    # 2) Agent 1 — unified_profile.dominant_mental_state
    raw = profile.get("dominant_mental_state")
    if raw and (mapped := _normalise(raw)):
        return mapped, "agent_1"

    # 3) Agent 1 — nested under aggregated_signals.nlp
    raw = _safe_get(profile, "aggregated_signals", "nlp", "dominant_mental_state")
    if raw and (mapped := _normalise(raw)):
        return mapped, "agent_1"

    # 4) Last resort: peek directly at the NLP model output
    raw = _safe_get(
        progress.model_outputs or {},
        "nlp_mental_health_model", "prediction", "dominant_mental_state",
    ) or _safe_get(
        progress.model_outputs or {},
        "nlp_mental_health_model", "prediction", "predicted_label",
    )
    if raw and (mapped := _normalise(raw)):
        return mapped, "model_layer"

    logger.warning(
        "[progress=%s] Could not resolve disorder — using NORMAL fallback",
        progress.id,
    )
    return Disorder.NORMAL, "fallback"


def _normalise(raw_value) -> Optional[str]:
    """Map a free-text label to a Disorder enum value, or None if unknown."""
    if not isinstance(raw_value, str):
        return None
    return _SYNONYMS.get(raw_value.strip().lower())


def _safe_get(d: dict, *keys, default=None):
    """Walk a nested dict safely — returns default if any key is missing."""
    cur = d
    for k in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k)
        if cur is None:
            return default
    return cur


def _extract_summary(final_output: dict) -> Optional[str]:
    """Pluck a short narrative for the audio page header, if Agent 3 wrote one."""
    return (
        final_output.get("plan_summary")
        or _safe_get(final_output, "diagnosis", "summary")
        or final_output.get("referral_message")
    )


def _load_recommendations(disorder_value: str):
    """Return (primary, list_of_alternatives) for the chosen Disorder."""
    qs = (
        DisorderRecommendation.objects
        .filter(disorder=disorder_value)
        .order_by("priority")
    )
    rows = list(qs)
    if not rows:
        # seed_audio.py wasn't run — fall back to NORMAL so we never 500.
        logger.error(
            "No DisorderRecommendation rows for %s — falling back to NORMAL",
            disorder_value,
        )
        rows = list(
            DisorderRecommendation.objects
            .filter(disorder=Disorder.NORMAL)
            .order_by("priority")
        )
    return rows[0], rows[1:]