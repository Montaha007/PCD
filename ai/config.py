# ai/config.py — UNIFIED MODEL PATHS
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# ── Model Artifact Paths ────────────────────────────────────────────────
SLEEP_CLASSIFIER_PATH = os.getenv(
    "SLEEP_CLASSIFIER_PATH",
    str(BASE_DIR / "models" / "best_insomnia_model.pkl")
)
SLEEP_SCALER_PATH = os.getenv(
    "SLEEP_SCALER_PATH",
    str(BASE_DIR / "models" / "sleep_scaler.pkl")
)
LIFESTYLE_MODEL_PATH = os.getenv(
    "LIFESTYLE_MODEL_PATH",
    str(BASE_DIR / "models" / "lifestyle_sleep_time_model.pkl")
)
LIFESTYLE_SCALER_PATH = os.getenv(
    "LIFESTYLE_SCALER_PATH",
    str(BASE_DIR / "models" / "lifestyle_scaler.pkl")
)

# ── LLM & Vector DB ────────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")