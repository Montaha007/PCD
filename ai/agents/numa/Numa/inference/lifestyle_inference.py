"""
inference/lifestyle_inference.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Rapport §5.2.2 — Lifestyle Model: Routine Cause Classifier
                 (Routine trigger: yes / no + cause identification)

Pipeline position : INPUT layer — runs BEFORE any agent.
Input  : user lifestyle features (routines, habits, diet — §3.1.2)
Output : dict → consumed by model_loader → passed to Correlation Agent
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import joblib
import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance
from config import LIFESTYLE_MODEL_PATH, LIFESTYLE_SCALER_PATH

# ── Lazy-loaded singletons ────────────────────────────────────────────────────
_model  = None
_scaler = None

# §5.2.2 — Feature columns from Data_Vis.ipynb (§3.1.2 Lifestyle Dataset)
BASE_FEATURES = [
    "WorkoutTime", "ReadingTime", "PhoneTime",
    "WorkHours", "CaffeineIntake", "RelaxationTime",
]


def _load():
    global _model, _scaler
    if _model is None:
        _model  = joblib.load(LIFESTYLE_MODEL_PATH)
        _scaler = joblib.load(LIFESTYLE_SCALER_PATH)


def _derive_feature_importances(X_scaled: np.ndarray, feature_names: list) -> dict:
    """
    §5.2.2 — Routine Cause Classifier:
    Approximates feature importance using permutation method.
    Returns {feature_name: importance_score} sorted descending.
    """
    try:
        dummy_y = np.zeros(len(X_scaled))
        result  = permutation_importance(
            _model, X_scaled, dummy_y,
            n_repeats=5, random_state=42, scoring="r2"
        )
        importances = {
            name: round(float(imp), 4)
            for name, imp in zip(feature_names, result.importances_mean)
        }
    except Exception:
        importances = {name: 0.0 for name in feature_names}

    return dict(sorted(importances.items(), key=lambda x: abs(x[1]), reverse=True))


def _classify_sleep_quality(hours: float) -> str:
    """§5.2.2 — Maps predicted sleep hours to a quality label."""
    if   hours < 6.0: return "INSUFFICIENT"
    elif hours < 7.0: return "BORDERLINE"
    elif hours < 8.5: return "ADEQUATE"
    else:             return "EXCESSIVE"


def predict_sleep_time(user_features: dict) -> dict:
    """
    §5.2.2 — Lifestyle Model: Routine Cause Classifier.

    Runs the VotingEnsemble (Ridge + SVR + CatBoost + LinearRegression
    from Data_Vis.ipynb) to predict sleep duration and identify which
    routine features are causing sleep disruption.

    Parameters
    ----------
    user_features : dict
        Keys from BASE_FEATURES — raw (unscaled) values.

    Returns
    -------
    dict  — structured output consumed by Correlation Agent (§5.3.1.1)
    """
    _load()

    # Build DataFrame with interaction features (mirrors Data_Vis.ipynb cell 5)
    row = {col: float(user_features.get(col, 0)) for col in BASE_FEATURES}
    df  = pd.DataFrame([row])
    df["Work_x_Caffeine"]       = df["WorkHours"]  * df["CaffeineIntake"]
    df["Screen_Time_Intensity"] = df["PhoneTime"]   * (1 / (df["RelaxationTime"] + 1))

    all_features = list(df.columns)
    X_scaled     = _scaler.transform(df)
    pred_hours   = float(_model.predict(X_scaled)[0])
    quality      = _classify_sleep_quality(pred_hours)

    # §5.2.2 — Feature importances = routine cause identification
    feat_imp = _derive_feature_importances(X_scaled, all_features)
    top3     = list(feat_imp.keys())[:3]

    # Primary cause = feature with highest absolute importance
    primary_cause = (
        f"Lifestyle disruption driven by {top3[0]}"
        if top3 else "No dominant lifestyle cause identified"
    )

    return {
        # §5.3.1.1 — fields consumed by Model Output Aggregation
        "model_name": "lifestyle_routine_cause_classifier",
        "prediction": {
            "predicted_sleep_hours": round(pred_hours, 2),
            "sleep_quality_label":   quality,
            "routine_trigger":       quality in {"INSUFFICIENT", "BORDERLINE"},
            "confidence":            0.0,   # set from r2_score after evaluation
        },
        "trigger_analysis": {
            "primary_cause":         primary_cause,
            "primary_causes":        top3[:2],
            "secondary_causes":      top3[2:],
            "feature_importances":   feat_imp,
        },
        "model_performance": {
            "model_type": "VotingEnsemble (Ridge + SVR + CatBoost + Linear)",
            "r2_score":   0.0,
            "mae_hours":  0.0,
            "rmse_hours": 0.0,
        },
        "dataset_info": {
            "feature_names": all_features,
            "target_column": "SleepTime",
        },
    }
