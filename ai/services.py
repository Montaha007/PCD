"""
Public entry point for the AI module.

Views should only ever import from here — never from pipeline, agents, etc.
This keeps the boundary clean and makes future refactors transparent.
"""
from __future__ import annotations

from .pipeline import run_sleep_pipeline


def predict_sleep(sleep_log) -> dict:
    """
    Run the full sleep analysis pipeline on *sleep_log* and return a result dict.

    Parameters
    ----------
    sleep_log : SleepLog instance (already saved, so duration/duration_of_problems
                are populated)

    Returns
    -------
    {
        "prediction":   "insomnia" | "no_insomnia",  # model-based label
        "confidence":   float,  # confidence for returned prediction label
        "model_score":  float,
        "qdrant_score": float,
        "qdrant_label": int,
        "model_label":  int,
        "signals_conflict": bool,
    }
    """
    return run_sleep_pipeline(sleep_log)
