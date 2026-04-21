"""
Full sleep-disorder prediction pipeline.

Order of operations
-------------------
1. Build raw feature dict from SleepLog instance.
2. Apply sleep_label_encoders.pkl  → encode any categorical string fields.
3. build_vector()                  → MinMaxScale (minmax_scaler_qdrant.pkl)
                                     → Qdrant query vector.
4. search()                        → top-5 similar cases + majority vote.
5. StandardScale (scaler.pkl)      → feed into best_insomnia_model.pkl.
6. Return unified result dict.
"""
from __future__ import annotations

import numpy as np

from .registry import get_kit
from .embedder import build_vector
from .retriever import search

DOMAIN = "sleep"

# Exact feature order — must match minmax_scaler_qdrant and scaler fit order.
FEATURE_COLS = [
    "Total_sleep_time(hour)",
    "Satisfaction_of_sleep",
    "Late_night_sleep",
    "Wakeup_frequently_during_sleep",
    "Sleep_at_daytime",
    "Drowsiness_tiredness",
    "Duration_of_this_problems(years)",
    "Recent_psychological_attack",
    "Afraid_of_getting_asleep",
]


def run_sleep_pipeline(sleep_log) -> dict:
    """
    Parameters
    ----------
    sleep_log : SleepLog Django model instance

    Returns
    -------
    {
        "prediction":        "insomnia" | "no_insomnia",
        "confidence":        float,   # confidence for the returned prediction
        "model_score":       float,   # model probability for class 1 (insomnia)
        "model_label":       int,
        "qdrant_score":      float,   # fraction of neighbours with insomnia
        "qdrant_label":      int,
        "signals_conflict":  bool,    # model label disagrees with qdrant vote
        "top_similar_cases": list[dict],
    }
    """
    kit = get_kit(DOMAIN)

    # ── 1. Raw feature dict ───────────────────────────────────────────────
    duration_hours = sleep_log.calculated_sleep_duration.total_seconds() / 3600
    raw = {
        "Total_sleep_time(hour)":           duration_hours,
        "Satisfaction_of_sleep":            int(sleep_log.satisfaction_of_sleep),
        "Late_night_sleep":                 int(sleep_log.late_night_sleep),
        "Wakeup_frequently_during_sleep":   int(sleep_log.wake_up_frequently),
        "Sleep_at_daytime":                 int(sleep_log.sleep_at_daytime),
        "Drowsiness_tiredness":             int(sleep_log.drowsiness_tiredness),
        "Duration_of_this_problems(years)": sleep_log.duration_of_problems,
        "Recent_psychological_attack":      int(sleep_log.recent_psychological_attack),
        "Afraid_of_getting_asleep":         int(sleep_log.afraid_of_sleeping),
    }

    # ── 2. Label-encode categorical fields ───────────────────────────────
    encoded = dict(raw)
    for col, encoder in kit["label_encoders"].items():
        if col in encoded:
            encoded[col] = encoder.transform([str(encoded[col])])[0]

    # ── 3. MinMaxScale → Qdrant query vector ─────────────────────────────
    qdrant_vector = build_vector(encoded)

    # ── 4. Qdrant retrieval + majority vote ──────────────────────────────
    hits = search(qdrant_vector, DOMAIN)
    if hits:
        insomnia_count = sum(1 for h in hits if h["disorder"] == 1)
        qdrant_score   = insomnia_count / len(hits)
        qdrant_label   = 1 if insomnia_count > len(hits) / 2 else 0
    else:
        qdrant_score = 0.0
        qdrant_label = 0

    # ── 5. StandardScale → model prediction ──────────────────────────────
    feature_array = np.array([[encoded[col] for col in FEATURE_COLS]])
    X_scaled      = kit["model_scaler"].transform(feature_array)

    model     = kit["model"]
    raw_label = int(model.predict(X_scaled)[0])

    if hasattr(model, "predict_proba"):
        proba   = model.predict_proba(X_scaled)[0]
        classes = list(model.classes_)
        idx     = classes.index(1) if 1 in classes else -1
        model_prob = float(proba[idx]) if idx >= 0 else float(raw_label)
    else:
        model_prob = float(raw_label)

    # Keep model_score as P(insomnia) and derive user-facing confidence
    # from the same label source to avoid contradictory UI output.
    model_prob = max(0.0, min(1.0, model_prob))
    model_label = 1 if raw_label == 1 else 0
    prediction_confidence = model_prob if model_label == 1 else (1.0 - model_prob)

    # ── 6. Return unified result ──────────────────────────────────────────
    return {
        "prediction":        "insomnia" if model_label == 1 else "no_insomnia",
        "confidence":        round(prediction_confidence, 4),
        "model_score":       round(model_prob, 4),
        "model_label":       model_label,
        "qdrant_score":      round(qdrant_score, 4),
        "qdrant_label":      qdrant_label,
        "signals_conflict":  model_label != qdrant_label,
        "top_similar_cases": hits,
    }
