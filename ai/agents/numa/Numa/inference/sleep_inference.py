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
import numpy as np
from pathlib import Path
from collections import Counter
from config import (
    SLEEP_CLASSIFIER_PATH, SLEEP_SCALER_PATH,
    QDRANT_URL, QDRANT_API_KEY, QDRANT_COLLECTION
)

# ── Lazy-loaded singletons ────────────────────────────────────────────────────
_classifier = None
_scaler     = None
_qdrant     = None

# §5.2.1 — Feature columns from insomnia_combined_pipeline.ipynb
# Update this list to match your actual training columns (excluding target)
SLEEP_FEATURE_ORDER = [
    "Age", "Gender", "BMI", "PhysicalActivity",
    "SleepDuration", "QualityOfSleep", "HeartRate", "DailySteps",
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

    # Normalise for Qdrant (MinMax already applied by scaler)
    query_vec = feature_vec.flatten().tolist()

    hits = _qdrant.query_points(
        collection_name=QDRANT_COLLECTION,
        query=query_vec,
        limit=K_NEIGHBOURS,
        with_payload=True,
    ).points

    labels     = [h.payload.get("Disorder", "unknown") for h in hits]
    vote       = Counter(labels)
    predicted  = vote.most_common(1)[0][0] if vote else "unknown"
    confidence = vote.most_common(1)[0][1] / len(labels) if labels else 0.0

    return {
        "vote_counts":      dict(vote),
        "vote_confidence":  round(confidence, 4),
        "predicted_label":  predicted,
    }


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

    # Build and scale feature vector
    X = np.array([[user_features.get(col, 0) for col in SLEEP_FEATURE_ORDER]])
    X_scaled = _scaler.transform(X)

    # §5.2.1 — ML classifier prediction
    prediction  = _classifier.predict(X_scaled)[0]
    proba       = _classifier.predict_proba(X_scaled)[0]
    ml_conf     = float(proba.max())
    insomnia    = bool(int(prediction) == 1)

    # §5.1.3.1 — Qdrant kNN confirmation
    knn = _qdrant_knn_vote(X_scaled)

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
