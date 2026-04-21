"""
Converts an already-label-encoded feature dict into a MinMaxScaled float
vector suitable for Qdrant similarity search.

IMPORTANT: use minmax_scaler_qdrant.pkl here — NOT scaler.pkl (StandardScaler).
           scaler.pkl is reserved exclusively for the classifier's predict path.
"""
from __future__ import annotations

import pandas as pd

from .registry import get_kit

DOMAIN = "sleep"


def build_vector(encoded: dict) -> list[float]:
    """
    Parameters
    ----------
    encoded : dict
        Feature dict **after** LabelEncoder has been applied to every
        categorical column.  Keys must match feature_columns.json exactly.

    Returns
    -------
    list[float]
        MinMaxScaled values in the order defined by feature_columns.json,
        ready to send as a Qdrant query vector.
    """
    kit = get_kit(DOMAIN)
    df = pd.DataFrame([encoded], columns=kit["feature_columns"])
    scaled = kit["qdrant_scaler"].transform(df)
    return scaled[0].tolist()
