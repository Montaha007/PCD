"""
model_loader.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Rapport §5.2 → §5.3 bridge
Runs all three inference modules in real-time when a user submits data,
then formats outputs for the Correlation Agent (§5.3.1.1).
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import logging
from datetime import datetime, timezone
from typing import Any

from inference import predict_insomnia, predict_sleep_time, predict_mental_state

logger = logging.getLogger(__name__)


def run_all_models(user_data: dict) -> dict[str, Any]:
    """
    §5.2 — Runs all three model inference modules in real-time.

    Parameters
    ----------
    user_data : dict with three sub-dicts:
        user_data["sleep_features"]     → §5.2.1 Sleep Model features
        user_data["lifestyle_features"] → §5.2.2 Lifestyle Model features
        user_data["journal_text"]       → §5.2.3 NLP Model free-text

    Returns
    -------
    dict with keys: sleep_model, lifestyle_model, nlp_mental_health_model
    Ready to be passed to crew.run_pipeline() → Correlation Agent §5.3.1.
    """
    user_id = user_data.get("user_id", "unknown")
    logger.info("§5.2 Running all three model inferences for user=%s", user_id)

    # §5.2.1 — Sleep Model: Binary Classifier (Insomnia yes/no)
    sleep_result = predict_insomnia(
        user_data.get("sleep_features", {})
    )
    logger.info(
        "§5.2.1 Sleep Model: insomnia=%s  conf=%.2f",
        sleep_result["prediction"]["insomnia_detected"],
        sleep_result["prediction"]["confidence"],
    )

    # §5.2.2 — Lifestyle Model: Routine Cause Classifier
    lifestyle_result = predict_sleep_time(
        user_data.get("lifestyle_features", {})
    )
    logger.info(
        "§5.2.2 Lifestyle Model: sleep=%.1fh  quality=%s  trigger=%s",
        lifestyle_result["prediction"]["predicted_sleep_hours"],
        lifestyle_result["prediction"]["sleep_quality_label"],
        lifestyle_result["prediction"]["routine_trigger"],
    )

    # §5.2.3 — NLP Model: Sentiment + Cause Extraction
    nlp_result = predict_mental_state(
        user_data.get("journal_text", "")
    )
    logger.info(
        "§5.2.3 NLP Model: state=%s  conf=%.2f",
        nlp_result["prediction"]["dominant_mental_state"],
        nlp_result["prediction"]["confidence"],
    )

    return {
        "user_id":   user_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),

        # §5.3.1.1 — keys consumed by Correlation Agent Model Output Aggregation
        "sleep_model":             sleep_result,
        "lifestyle_model":         lifestyle_result,
        "nlp_mental_health_model": nlp_result,
    }
