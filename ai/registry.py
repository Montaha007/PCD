"""
Lazy-loading artifact registry.

Artifacts per domain are loaded once and cached in memory.

sleep domain files expected in ai/models/:
  best_insomnia_model.pkl     — trained classifier
  minmax_scaler_qdrant.pkl    — MinMaxScaler  → Qdrant query vectors
  sleep_scaler.pkl            — StandardScaler → model .predict() path only
  sleep_label_encoders.pkl    — dict {col: fitted LabelEncoder}
  sleep_feature_columns.json  — ordered list of 9 feature column names

lifestyle domain files expected in ai/models/:
  lifestyle_sleep_time_model.pkl — trained regressor (only file; no scaler)
  lifestyle_scaler.pkl          — StandardScaler → model .predict() path only
  lifestyle_feature_columns.json — ordered list of feature column names
"""
from __future__ import annotations

import json
import joblib
from pathlib import Path

MODELS_DIR = Path(__file__).parent / "models"

_STEMS: dict[str, dict[str, str]] = {
    "sleep": {
        "model":           "best_insomnia_model",
        "qdrant_scaler":   "minmax_scaler_qdrant",
        "model_scaler":    "sleep_scaler",
        "label_encoders":  "sleep_label_encoders",
        "feature_columns": "sleep_feature_columns",
    },
    "lifestyle": {
        "model": "lifestyle_sleep_time_model",
        "model_scaler": "lifestyle_scaler",
        "feature_columns": "lifestyle_feature_columns",
    },
}

_cache: dict[str, dict] = {}


def get_kit(domain: str) -> dict:
    """Return (and cache) all artifacts for *domain*."""
    if domain in _cache:
        return _cache[domain]

    stems = _STEMS.get(domain)
    if stems is None:
        raise ValueError(f"No artifact stems registered for domain '{domain}'.")

    kit: dict = {}

    # Model is always required
    kit["model"] = joblib.load(MODELS_DIR / f"{stems['model']}.pkl")

    # Optional artifacts — only load if declared for this domain
    if "qdrant_scaler" in stems:
        kit["qdrant_scaler"] = joblib.load(MODELS_DIR / f"{stems['qdrant_scaler']}.pkl")
    if "model_scaler" in stems:
        kit["model_scaler"] = joblib.load(MODELS_DIR / f"{stems['model_scaler']}.pkl")
    if "label_encoders" in stems:
        kit["label_encoders"] = joblib.load(MODELS_DIR / f"{stems['label_encoders']}.pkl")
    if "feature_columns" in stems:
        with open(MODELS_DIR / f"{stems['feature_columns']}.json") as f:
            kit["feature_columns"] = json.load(f)

    _cache[domain] = kit
    return kit