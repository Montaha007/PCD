"""
Qdrant connection singleton.

Reads QDRANT_URL and QDRANT_API_KEY from Django settings.
The client is created once and reused for the lifetime of the process.
──────────────────────────────────────────────────────────────────────────────
Singleton clients for Qdrant, Neo4j, and Groq.
 
MODIFICATION LOG (keep existing code untouched — additions marked NEW):
  • Qdrant client singleton — EXISTING (do not touch)
  • Neo4j driver singleton  — NEW
  • Groq client singleton   — NEW
 
All credentials come from Django settings, which in turn read from environment
variables. Add these to your .env / secret manager:
 
    QDRANT_URL          — existing
    QDRANT_API_KEY      — existing
    NEO4J_URI           — new  (e.g. neo4j+s://<id>.databases.neo4j.io)
    NEO4J_USERNAME      — new  (usually "neo4j")
    NEO4J_PASSWORD      — new
    GROQ_API_KEY        — new
 
Then expose them in settings.py:
 
    import os
    QDRANT_URL     = os.environ["QDRANT_URL"]
    QDRANT_API_KEY = os.environ["QDRANT_API_KEY"]
    NEO4J_URI      = os.environ["NEO4J_URI"]
    NEO4J_USERNAME = os.environ["NEO4J_USERNAME"]
    NEO4J_PASSWORD = os.environ["NEO4J_PASSWORD"]
    GROQ_API_KEY   = os.environ["GROQ_API_KEY"]
"""
from __future__ import annotations
from django.conf import settings
from qdrant_client import QdrantClient
from qdrant_client import QdrantClient
from neo4j import GraphDatabase
from groq import Groq
 
_client: QdrantClient | None = None


def get_qdrant_client() -> QdrantClient:
    return get_qdrant()


def get_qdrant() -> QdrantClient:
    global _client
    if _client is None:
        from django.conf import settings
        _client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY,
        )
    return _client

# ══════════════════════════════════════════════════════════════════════════════
# NEW — Neo4j driver singleton
# ══════════════════════════════════════════════════════════════════════════════
 
_neo4j_driver = None
 
 
def get_neo4j_driver():
    """
    Return the module-level Neo4j driver, creating it on first call.
 
    The driver manages its own connection pool internally — do not call
    driver.close() except at application shutdown (Django AppConfig.ready /
    signal). Sessions must be opened per-operation:
 
        with get_neo4j_driver().session() as session:
            session.run(...)
    """
    global _neo4j_driver
    if _neo4j_driver is None:
        _neo4j_driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD),
        )
    return _neo4j_driver
 
 
# ══════════════════════════════════════════════════════════════════════════════
# NEW — Groq client singleton
# ══════════════════════════════════════════════════════════════════════════════
 
_groq_client: Groq | None = None
 
 
def get_groq_client() -> Groq:
    """
    Return the module-level Groq client, creating it on first call.
    The Groq SDK client is stateless between calls — one instance is fine.
    """
    global _groq_client
    if _groq_client is None:
        _groq_client = Groq(api_key=settings.GROQ_API_KEY)
    return _groq_client
