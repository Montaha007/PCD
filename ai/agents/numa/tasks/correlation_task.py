"""
tasks/correlation_task.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Rapport §5.4.2 — Workflow Management: Task 1 of 3
         §5.4.3 — Data Flow: Model Layer → Correlation Agent
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import json
from crewai import Task, Agent


def _slim_outputs(outputs: dict) -> dict:
    """Extract only the fields the Correlation Agent needs — keeps the payload small."""
    sm = outputs.get("sleep_model", {})
    lm = outputs.get("lifestyle_model", {})
    nm = outputs.get("nlp_mental_health_model", {})
    return {
        "user_id": outputs.get("user_id"),
        "sleep_model": {
            "insomnia_detected":  sm.get("prediction", {}).get("insomnia_detected"),
            "predicted_disorder": sm.get("prediction", {}).get("predicted_disorder"),
            "confidence":         sm.get("prediction", {}).get("confidence"),
            "vote_counts":        sm.get("qdrant_classification", {}).get("vote_counts"),
            "vote_confidence":    sm.get("qdrant_classification", {}).get("vote_confidence"),
            "classifier_name":    sm.get("best_ml_classifier", {}).get("name"),
            "accuracy":           sm.get("best_ml_classifier", {}).get("accuracy"),
            "f1_score":           sm.get("best_ml_classifier", {}).get("f1_score"),
        },
        "lifestyle_model": {
            "predicted_sleep_hours": lm.get("prediction", {}).get("predicted_sleep_hours"),
            "sleep_quality_label":   lm.get("prediction", {}).get("sleep_quality_label"),
            "routine_trigger":       lm.get("prediction", {}).get("routine_trigger"),
            "confidence":            lm.get("prediction", {}).get("confidence"),
            "primary_cause":         lm.get("trigger_analysis", {}).get("primary_cause"),
            "primary_causes":        lm.get("trigger_analysis", {}).get("primary_causes"),
            "secondary_causes":      lm.get("trigger_analysis", {}).get("secondary_causes"),
            "feature_importances":   lm.get("trigger_analysis", {}).get("feature_importances"),
            "r2_score":              lm.get("model_performance", {}).get("r2_score"),
            "mae_hours":             lm.get("model_performance", {}).get("mae_hours"),
        },
        "nlp_mental_health_model": {
            "dominant_mental_state": nm.get("prediction", {}).get("dominant_mental_state"),
            "confidence":            nm.get("prediction", {}).get("confidence"),
            "primary_emotion":       nm.get("sentiment_analysis", {}).get("primary_emotion"),
            "secondary_emotions":    nm.get("sentiment_analysis", {}).get("secondary_emotions"),
            "root_causes_extracted": nm.get("root_causes_extracted"),
            "top_symptoms":          nm.get("knowledge_graph", {}).get("top_symptoms"),
            "top_emotions":          nm.get("knowledge_graph", {}).get("top_emotions"),
            "top_triggers":          nm.get("knowledge_graph", {}).get("top_triggers"),
            "nlp_accuracy":          nm.get("system_evaluation", {}).get("accuracy_on_test_cases"),
        },
    }


def build_correlation_task(agent: Agent, model_outputs: dict) -> Task:
    """
    §5.4.2 — Task 1 (FIRST in sequential pipeline).
    §5.4.3 — Data flow: inference layer → Correlation Agent.
    """
    data_json = json.dumps(_slim_outputs(model_outputs))

    description = f"""TASK 1/3 — CORRELATION AGENT §5.3.1
Input data from the §5.2 Model Layer:
{data_json}

Apply §5.3.1.1–§5.3.1.4 (as defined in your role):
- Aggregate all signals, compute confidence weights (5 steps), detect conflicts (5 types).
- Output ONLY the Unified Insomnia Profile JSON. No prose, no markdown, no code fences.
- Floats to 4 decimal places. Normalised weights must sum to 1.0 (±0.001)."""

    return Task(
        description=description,
        agent=agent,
        expected_output=(
            "Single valid JSON — Unified Insomnia Profile (§5.3.1.4). "
            "Keys: user_id, profile_timestamp, insomnia_detected, primary_disorder, "
            "insomnia_type, overall_confidence, confidence_tier, confidence_weighting, "
            "aggregated_signals, conflicts_detected, missing_signals, profile_summary, flags."
        ),
    )
