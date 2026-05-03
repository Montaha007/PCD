"""
config.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Rapport §7.1.2 — Software Environment
Central configuration — all secrets loaded from .env
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import os
import logging
from typing import Any

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover - fallback for minimal environments
    def load_dotenv() -> bool:
        return False


logger = logging.getLogger(__name__)


load_dotenv()
import sys
from pathlib import Path

# Import parent config
parent_config_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(parent_config_path))

from ai.config import (
    GROQ_API_KEY, QDRANT_URL, QDRANT_API_KEY,
    NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD,
    SLEEP_CLASSIFIER_PATH, SLEEP_SCALER_PATH,
    LIFESTYLE_MODEL_PATH, LIFESTYLE_SCALER_PATH,
)


# ── §5.1.3.3  LLM — Agent Layer ───────────────────────────────────────────────
LLM_MODEL       = os.getenv("LLM_MODEL", "groq/llama-3.3-70b-versatile")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.2"))
_api_key        = os.getenv("GROQ_API_KEY") or os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY", "")

def _build_agent_llm() -> Any | None:
    """Build CrewAI LLM if dependency is available; otherwise return None."""
    try:
        from crewai.llm import LLM
    except Exception as exc:
        logger.warning("CrewAI LLM unavailable in current environment: %s", exc)
        return None

    return LLM(
        model=LLM_MODEL,
        api_key=_api_key,
        temperature=LLM_TEMPERATURE,
        max_tokens=3000,
    )


AGENT_LLM = _build_agent_llm()

# ── §5.1.3.1  Qdrant — Shared Vector Store ────────────────────────────────────
QDRANT_SLEEP_COLLECTION   = os.getenv("QDRANT_SLEEP_COLLECTION", "sleep_disorders")
QDRANT_SEMANTIC_COLLECTION = os.getenv("QDRANT_SEMANTIC_COLLECTION", "PCD_Sleep_Disorder+Semantic")

# Backwards-compat: older modules still import QDRANT_COLLECTION.
# Treat it as the semantic (384-dim) collection used by NLP.
QDRANT_COLLECTION = QDRANT_SEMANTIC_COLLECTION
# ── §5.3  Agent Layer — CrewAI settings ───────────────────────────────────────
AGENT_VERBOSE = True
CREW_VERBOSE  = True

# ── §5.3.1.2  Confidence Weighting thresholds ─────────────────────────────────
CONFIDENCE_UNRELIABLE = 0.40   # below → ×0.50 penalty
CONFIDENCE_UNCERTAIN  = 0.60   # below → ×0.75 penalty
CONFIDENCE_MODERATE   = 0.75   # below → ×0.90 penalty
                                # above → ×1.00 (no penalty)
