"""
Converts an already-label-encoded feature dict into a MinMaxScaled float
vector suitable for Qdrant similarity search.

IMPORTANT: use minmax_scaler_qdrant.pkl here — NOT scaler.pkl (StandardScaler).
           scaler.pkl is reserved exclusively for the classifier's predict path.
"""
from __future__ import annotations

import requests
import pandas as pd

from django.conf import settings
from .registry import get_kit


def embed(text: str) -> list[float]:
    """
    Embed text using all-MiniLM-L6-v2 via HuggingFace InferenceClient (remote).
    Returns a 384-dim vector matching the Qdrant journal collection.
    """
    from huggingface_hub import InferenceClient
    client = InferenceClient(api_key=settings.HF_API_KEY)
    result = client.feature_extraction(
        text,
        model="sentence-transformers/all-MiniLM-L6-v2",
    )
    # result is a numpy array of shape (384,) or (1, 384)
    import numpy as np
    arr = np.array(result)
    if arr.ndim == 2:
        arr = arr[0]
    return arr.tolist()

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
