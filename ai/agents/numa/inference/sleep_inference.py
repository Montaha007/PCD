"""
inference/sleep_inference.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Rapport §5.2.1 — Sleep Model: Binary Classifier (Insomnia: Yes / No)
         §5.1.3.1 — Role in Sleep Model (Qdrant vector retrieval)

Pipeline position : INPUT layer — runs BEFORE any agent.
Input  : user sleep log features (hours, quality, patterns)
Output : dict → consumed by model_loader → passed to Correlation Agent
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import joblib
import math
import numpy as np
import pandas as pd
from collections import Counter

from ai.registry import get_kit

from ..config import (
    SLEEP_CLASSIFIER_PATH,
    SLEEP_SCALER_PATH,
    QDRANT_URL,
    QDRANT_API_KEY,
    QDRANT_SLEEP_COLLECTION,
)

# ── Lazy-loaded singletons ────────────────────────────────────────────────────
_classifier = None
_scaler     = None
_qdrant     = None

# §5.2.1 — Feature columns from insomnia_combined_pipeline.ipynb
# Update this list to match your actual training columns (excluding target)
SLEEP_FEATURE_ORDER = [
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

# §5.1.3.1 — Qdrant collection name (shared with NLP model)
K_NEIGHBOURS = 5


def _load():
    """Lazy-load classifier, scaler, and Qdrant client once."""
    global _classifier, _scaler, _qdrant
    if _classifier is None:
        _classifier = joblib.load(SLEEP_CLASSIFIER_PATH)
        _scaler     = joblib.load(SLEEP_SCALER_PATH)
    if _qdrant is None and QDRANT_URL:
        from qdrant_client import QdrantClient
        _qdrant = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)


def _qdrant_knn_vote(feature_vec: np.ndarray) -> dict:
    """
    §5.1.3.1 — Role in Sleep Model:
    Performs Qdrant cosine-similarity kNN retrieval to confirm
    the ML classifier prediction via nearest-neighbour voting.
    Returns vote_counts and vote_confidence.
    """
    if _qdrant is None:
        return {"vote_counts": {}, "vote_confidence": 0.0, "predicted_label": "unknown"}

    # Normalise for Qdrant (MinMax must already be applied by caller)
    query_vec = feature_vec.flatten().tolist()

    try:
        hits = _qdrant.query_points(
            collection_name=QDRANT_SLEEP_COLLECTION,
            query=query_vec,
            limit=K_NEIGHBOURS,
            with_payload=True,
        ).points
    except Exception:
        return {"vote_counts": {}, "vote_confidence": 0.0, "predicted_label": "unknown"}

    labels = [
        h.payload.get("label", h.payload.get("Disorder", h.payload.get("disorder", "unknown")))
        for h in hits
    ]
    vote       = Counter(labels)
    predicted  = vote.most_common(1)[0][0] if vote else "unknown"
    confidence = vote.most_common(1)[0][1] / len(labels) if labels else 0.0

    return {
        "vote_counts":      dict(vote),
        "vote_confidence":  round(confidence, 4),
        "predicted_label":  predicted,
    }


def _build_qdrant_sleep_vector(encoded: dict) -> list[float]:
    """Build a 9-dim MinMaxScaled vector for the sleep Qdrant collection."""
    kit = get_kit("sleep")
    df = pd.DataFrame([encoded], columns=kit["feature_columns"])
    scaled = kit["qdrant_scaler"].transform(df)
    return scaled[0].tolist()

def predict_insomnia(user_features: dict) -> dict:
    """
    §5.2.1 — Sleep Model Binary Classifier.

    Runs the best ML classifier (SVM / RF / KNN from
    insomnia_combined_pipeline.ipynb) on user sleep features,
    then confirms via Qdrant kNN vote (§5.1.3.1).

    Parameters
    ----------
    user_features : dict
        Keys from SLEEP_FEATURE_ORDER — raw (unscaled) values.

    Returns
    -------
    dict  — structured output consumed by Correlation Agent (§5.3.1.1)
    """
    _load()

    # Build feature dict in exact training order
    raw = {col: user_features.get(col, 0) for col in SLEEP_FEATURE_ORDER}

    # Apply the same label-encoding rules as the canonical sleep pipeline
    kit = get_kit("sleep")
    encoded = dict(raw)
    for col, encoder in kit.get("label_encoders", {}).items():
        if col in encoded:
            encoded[col] = encoder.transform([str(encoded[col])])[0]

    # Model path uses StandardScaler
    X = np.array([[encoded.get(col, 0) for col in SLEEP_FEATURE_ORDER]], dtype=float)
    X_scaled = _scaler.transform(X)

    # §5.2.1 — ML classifier prediction
    prediction  = _classifier.predict(X_scaled)[0]
    
    insomnia = bool(int(prediction) == 1)

# Confidence:
# - use predict_proba if available
# - else use decision_function magnitude mapped to (0.5..1.0)
    ml_conf = 0.5
    if hasattr(_classifier, "predict_proba"):
        proba = _classifier.predict_proba(X_scaled)[0]
        ml_conf = float(max(proba))
    elif hasattr(_classifier, "decision_function"):
        score = float(_classifier.decision_function(X_scaled)[0])
        ml_conf = 1.0 / (1.0 + math.exp(-abs(score)))

    # §5.1.3.1 — Qdrant kNN confirmation
    # IMPORTANT: sleep Qdrant collection stores MinMaxScaled 9-dim feature vectors.
    qdrant_vec = _build_qdrant_sleep_vector(encoded)
    knn = _qdrant_knn_vote(np.asarray(qdrant_vec, dtype=float))

    # Overall confidence = average of ML confidence + kNN vote confidence
    overall_conf = round((ml_conf + knn["vote_confidence"]) / 2, 4)

    return {
        # §5.3.1.1 — fields consumed by Model Output Aggregation
        "model_name": "sleep_binary_classifier",
        "prediction": {
            "insomnia_detected":  insomnia,
            "predicted_disorder": str(prediction),
            "confidence":         overall_conf,
        },
        "qdrant_classification": {
            "predicted_label":   knn["predicted_label"],
            "vote_counts":       knn["vote_counts"],
            "vote_confidence":   knn["vote_confidence"],
        },
        "best_ml_classifier": {
            "name":     type(_classifier).__name__,
            "accuracy": 0.0,   # filled after offline evaluation
            "f1_score": 0.0,
        },
        "dataset_info": {
            "feature_count":    len(SLEEP_FEATURE_ORDER),
            "target_column":    "Disorder",
            "unique_disorders": [],
        },
    }
