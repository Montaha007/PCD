"""
inference/nlp_inference.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Rapport §5.2.3 — NLP Mental Health Model: Sentiment + Cause Extraction
         §5.1.3.1 — Role in NLP Model (Qdrant semantic retrieval)
         §5.1.3.2 — Graph-Based Knowledge Modeling — Neo4j
                    (Causal Reasoning Structure used here for entity enrichment)

Pipeline position : INPUT layer — runs BEFORE any agent.
Input  : user journal entries (free-text, daily logs — §3.1.3)
Output : dict → consumed by model_loader → passed to Correlation Agent
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import os
from collections import Counter, defaultdict
from config import (
    QDRANT_URL, QDRANT_API_KEY, QDRANT_COLLECTION,
    NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD
)

# ── Lazy-loaded singletons ────────────────────────────────────────────────────
_embed_model = None
_qdrant      = None
_neo4j       = None

# §5.2.3 — NLP model config (mirrors nlpqdrantfinale.ipynb)
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
K_NEIGHBOURS    = 10
MAJORITY_WEIGHT = 0.5   # blend: 0.5 majority + 0.5 score-weighted

# §5.2.3 — Mental health classes the NLP model can predict
MENTAL_HEALTH_CLASSES = [
    "depression", "anxiety", "stress",
    "bipolar", "suicidal", "personality disorder", "normal"
]


def _load():
    """Lazy-load embedding model, Qdrant client, and Neo4j driver."""
    global _embed_model, _qdrant, _neo4j
    if _embed_model is None:
        from sentence_transformers import SentenceTransformer
        _embed_model = SentenceTransformer(EMBEDDING_MODEL)
    if _qdrant is None and QDRANT_URL:
        from qdrant_client import QdrantClient
        _qdrant = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    if _neo4j is None and NEO4J_URI:
        from neo4j import GraphDatabase
        try:
            _neo4j = GraphDatabase.driver(
                NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
            )
        except Exception:
            _neo4j = None


def _qdrant_semantic_search(text: str) -> dict:
    """
    §5.1.3.1 — Role in NLP Model:
    Encodes journal text with all-MiniLM-L6-v2, performs cosine-similarity
    search in Qdrant (collection PCD_Sleep_Disorder+Semantic built with
    SemanticChunker SDPM), and applies hybrid voting to classify mental state.
    """
    if _qdrant is None:
        return {"predicted_label": "unknown", "confidence": 0.0,
                "vote_counts": {}, "sources": []}

    query_vec = _embed_model.encode(text).tolist()
    hits = _qdrant.query_points(
        collection_name=QDRANT_COLLECTION,
        query=query_vec,
        limit=K_NEIGHBOURS,
        with_payload=True,
    ).points

    # §5.2.3 — Deduplicate by source_id (mirrors nlpqdrantfinale.ipynb logic)
    source_results = {}
    for hit in hits:
        sid   = hit.payload.get("source_id")
        lbl   = hit.payload.get("status", "unknown")
        score = hit.score
        if sid not in source_results or score > source_results[sid]["score"]:
            source_results[sid] = {"status": lbl, "score": score}

    unique  = list(source_results.values())
    n       = len(unique) or 1
    tot_s   = sum(v["score"] for v in unique) or 1

    # Hybrid vote: majority count + score-weighted
    majority_votes  = Counter(v["status"] for v in unique)
    weighted_scores = defaultdict(float)
    for v in unique:
        weighted_scores[v["status"]] += v["score"]

    final_scores = {}
    for lbl in majority_votes:
        m = majority_votes[lbl] / n
        w = weighted_scores[lbl] / tot_s
        final_scores[lbl] = MAJORITY_WEIGHT * m + (1 - MAJORITY_WEIGHT) * w

    predicted  = max(final_scores, key=final_scores.get) if final_scores else "unknown"
    confidence = round(final_scores.get(predicted, 0.0), 4)

    return {
        "predicted_label": predicted,
        "confidence":      confidence,
        "vote_counts":     dict(majority_votes),
        "sources":         unique[:5],
    }


def _neo4j_graph_entities() -> dict:
    """
    §5.1.3.2 — Graph-Based Knowledge Modeling (Neo4j):
    Retrieves the most-connected Symptoms, Emotions, and Triggers from
    the Neo4j knowledge graph (built via neo4j_graphrag.ipynb).
    These entities enrich the root_causes_extracted field.
    """
    empty = {"top_symptoms": [], "top_emotions": [], "top_triggers": [], "node_counts": {}}
    if _neo4j is None:
        return empty
    try:
        with _neo4j.session() as s:
            symptoms = [r["name"] for r in s.run(
                "MATCH (n:Symptom)-[r]-() RETURN n.name AS name, "
                "count(r) AS c ORDER BY c DESC LIMIT 5"
            ).data()]
            emotions = [r["name"] for r in s.run(
                "MATCH (n:Emotion)-[r]-() RETURN n.name AS name, "
                "count(r) AS c ORDER BY c DESC LIMIT 5"
            ).data()]
            triggers = [r["name"] for r in s.run(
                "MATCH (n:Trigger)-[r]-() RETURN n.name AS name, "
                "count(r) AS c ORDER BY c DESC LIMIT 5"
            ).data()]
            counts = {}
            for label in ["Document", "Chunk", "MentalHealthCondition",
                          "Symptom", "Emotion", "Trigger"]:
                counts[label] = s.run(
                    f"MATCH (n:{label}) RETURN count(n) AS c"
                ).single()["c"]
        return {
            "top_symptoms": symptoms,
            "top_emotions": emotions,
            "top_triggers": triggers,
            "node_counts":  counts,
        }
    except Exception:
        return empty


def predict_mental_state(journal_text: str) -> dict:
    """
    §5.2.3 — NLP Mental Health Model: Sentiment and Cause Extraction.

    Architecture (from nlpqdrantfinale.ipynb + neo4j_graphrag.ipynb):
      1. SemanticChunker (SDPM) chunks the text  [done offline at indexing]
      2. all-MiniLM-L6-v2 encodes the query
      3. Qdrant cosine-similarity search → top-K chunks (§5.1.3.1)
      4. Hybrid voting (majority + score-weighted) → mental state label
      5. Neo4j graph traversal → entity enrichment (§5.1.3.2)

    Parameters
    ----------
    journal_text : str
        Raw journal entry / free-text from the user (§3.1.3).

    Returns
    -------
    dict  — structured output consumed by Correlation Agent (§5.3.1.1)
    """
    _load()

    # §5.2.3 — Qdrant semantic retrieval + hybrid voting
    qdrant_result = _qdrant_semantic_search(journal_text)

    # §5.1.3.2 — Neo4j graph entity enrichment
    graph = _neo4j_graph_entities()

    predicted  = qdrant_result["predicted_label"]
    confidence = qdrant_result["confidence"]

    return {
        # §5.3.1.1 — fields consumed by Model Output Aggregation
        "model_name":   "nlp_mental_health_model",
        "architecture": "Qdrant (SemanticChunker SDPM + all-MiniLM-L6-v2) + Neo4j GraphRAG",
        "prediction": {
            "dominant_mental_state": predicted,
            "confidence":            confidence,
            "classes_available":     MENTAL_HEALTH_CLASSES,
        },
        "sentiment_analysis": {
            "primary_emotion":    predicted,
            "secondary_emotions": [k for k in qdrant_result["vote_counts"] if k != predicted],
            "intensity":          confidence,
        },
        "root_causes_extracted": graph["top_triggers"],
        "knowledge_graph": {
            "top_symptoms": graph["top_symptoms"],
            "top_emotions": graph["top_emotions"],
            "top_triggers": graph["top_triggers"],
            "node_counts":  graph["node_counts"],
        },
        "system_evaluation": {
            "accuracy_on_test_cases": 0.0,  # filled after offline evaluation
        },
        "vector_store": {
            "collection_name": QDRANT_COLLECTION,
            "embedding_model": EMBEDDING_MODEL,
            "vote_counts":     qdrant_result["vote_counts"],
        },
    }
