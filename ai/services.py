"""
Public entry point for the AI module.

Views should only ever import from here — never from pipeline, agents, etc.
This keeps the boundary clean and makes future refactors transparent.
──────────────────────────────────────────────────────────────────────────────
MODIFICATION LOG:
  • All code above the "NEW ADDITION" marker is your existing service layer.
    Left as a placeholder — paste yours back verbatim.
  • analyze_journal() is NEW.
 
analyze_journal() is the single public entry point that journal/views.py calls.
It owns the full text-to-prediction chain:
  raw text → clean → embed + retrieve → LLM → structured dict
"""
from __future__ import annotations
from .preprocessor import JournalPreprocessor
from .pipeline import graphrag_answer
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
# ══════════════════════════════════════════════════════════════════════════════
# NEW ADDITION — analyze_journal
# ══════════════════════════════════════════════════════════════════════════════
 
def analyze_journal(text: str) -> dict:
    """
    Orchestrate the full mental-health analysis pipeline for a journal entry.
 
    Args:
        text: Raw (uncleaned) journal entry string from the request body.
 
    Returns:
        {
          "predicted_label": str,   e.g. "depression", "anxiety", "normal"
          "confidence":      float, 0.0 – 1.0
          "analysis_text":   str,   clinical paragraph from Groq
        }
 
    Raises:
        ValueError: If text is empty after cleaning.
        Exception:  Propagates Qdrant / Neo4j / Groq errors upstream.
    """
    # Step 1 — Preprocess (must match Qdrant collection build pipeline)
    cleaned: str = JournalPreprocessor().clean(text)
 
    if not cleaned:
        raise ValueError("Journal text is empty after preprocessing.")
 
    # Step 2 — GraphRAG pipeline
    result: dict = graphrag_answer(cleaned)
 
    return result