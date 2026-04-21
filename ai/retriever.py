"""
Qdrant vector search — returns the top-K nearest neighbours with their
disorder labels and similarity scores.
MODIFICATION LOG:
  • Everything above the "NEW ADDITION" marker is your existing retriever code.
    It has not been touched.
  • hybrid_retrieve() and its helpers are NEW.
 
hybrid_retrieve() implements the exact same two-phase pipeline used in
neo4j-graphrag_5_.ipynb (section 14) and nlpqdrantfinale.ipynb:
 
  Phase 1  — Qdrant semantic search
    - Embed cleaned text with the existing embedder (all-MiniLM-L6-v2)
    - Retrieve top-k chunks from PCD_Sleep_Disorder+Semantic
    - Deduplicate by source_id, keep best chunk score per source
    - Hybrid vote: 0.5 * majority_score + 0.5 * score_weighted_score
 
  Phase 2  — Neo4j graph expansion
    - UNWIND retrieved chunk_ids
    - MATCH Chunk -[:MENTIONS]-> entity -[r]-> related
    - Collect unique entities and human-readable relationship paths
 
Returns a dict with keys:
    vector_chunks    list[dict]  deduplicated Qdrant hits
    graph_entities   list[dict]  unique entities from Neo4j
    graph_paths      list[str]   "(entity:Type) -[REL]-> (related:Type)" strings
    merged_context   str         formatted context string ready for the LLM
    predicted_label  str         winning label from hybrid vote
    confidence       float       combined score of the winning label
"""
from __future__ import annotations
from collections import defaultdict
from django.conf import settings
from .client import get_qdrant
from .client import get_qdrant_client, get_neo4j_driver
from .embedder import embed
_TOP_K = 5
COLLECTION_NAME = "PCD_Sleep_Disorder+Semantic"
# Majority / score-weighted blend factor — mirrors notebook default (0.5 / 0.5)
MAJORITY_WEIGHT = 0.5
 

def _collection_for(domain: str) -> str:
    collections: dict = settings.QDRANT_COLLECTIONS
    if domain not in collections:
        raise ValueError(
            f"No Qdrant collection configured for domain '{domain}'. "
            f"Add it to QDRANT_COLLECTIONS in settings.py."
        )
    return collections[domain]


def _parse_label(payload: dict) -> int:
    """Normalize the stored Disorder field to 0 or 1."""
    raw = payload.get("label", payload.get("Disorder", payload.get("disorder", 0)))

    if isinstance(raw, bool):
        return int(raw)
    if isinstance(raw, (int, float)):
        return 1 if int(raw) == 1 else 0
    if isinstance(raw, str):
        v = raw.strip().lower()
        if v in {"1", "1.0", "insomnia", "true", "yes"}:
            return 1
        if v in {"0", "0.0", "no_insomnia", "no insomnia", "none", "false", "no"}:
            return 0
        try:
            return 1 if int(float(v)) == 1 else 0
        except ValueError:
            return 0
    return 0


def search(vector: list[float], domain: str) -> list[dict]:
    """
    Query Qdrant for the top-5 nearest neighbours of *vector*.

    Returns
    -------
    list of dicts:
        {
            "disorder":         int,   # 0 or 1
            "similarity_score": float,
            "payload":          dict,  # raw stored payload
        }
    """
    try:
        client = get_qdrant()
        points = client.query_points(
            collection_name=_collection_for(domain),
            query=vector,
            limit=_TOP_K,
            with_payload=True,
        ).points

        return [
            {
                "disorder":         _parse_label(p.payload),
                "similarity_score": round(float(p.score), 4),
                "payload":          p.payload,
            }
            for p in points
        ]
    except Exception:
        return []
def hybrid_retrieve(text: str, k: int = 10) -> dict:
    """
    Hybrid GraphRAG retriever combining Qdrant vector search + Neo4j graph
    traversal. Mirrors hybrid_retrieve() from neo4j-graphrag_5_.ipynb §14.
 
    Args:
        text: Pre-cleaned journal text (run through JournalPreprocessor first).
        k:    Number of Qdrant chunks to retrieve.
 
    Returns:
        {
          "vector_chunks":   list[dict],   # deduplicated Qdrant hits
          "graph_entities":  list[dict],   # unique graph entities
          "graph_paths":     list[str],    # readable relationship paths
          "merged_context":  str,          # formatted LLM context block
          "predicted_label": str,          # winning mental-health label
          "confidence":      float,        # combined score (0-1)
        }
    """
    qdrant = get_qdrant_client()
    driver = get_neo4j_driver()
 
    # ── Phase 1A: Qdrant semantic search ──────────────────────────────────
    query_vector: list[float] = embed(text)   # all-MiniLM-L6-v2, dim=384
 
    qdrant_hits = qdrant.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=k,
        with_payload=True,
    ).points
 
    # ── Phase 1B: Deduplicate by source_id, keep best chunk score ─────────
    # Exact logic from nlpqdrantfinale.ipynb predict_sleep_status()
    source_results: dict[int, dict] = {}
    for hit in qdrant_hits:
        sid   = hit.payload.get("source_id")
        label = hit.payload.get("status", "unknown")
        score = hit.score
        if sid not in source_results or score > source_results[sid]["score"]:
            source_results[sid] = {
                "chunk_id":  str(hit.id),
                "source_id": sid,
                "text":      hit.payload.get("text", ""),
                "status":    label,
                "score":     score,
            }
 
    vector_chunks: list[dict] = list(source_results.values())
 
    # ── Phase 1C: Hybrid voting ────────────────────────────────────────────
    # final[label] = 0.5 * (count / total) + 0.5 * (score_sum / total_score)
    predicted_label, confidence, _ = _hybrid_vote(vector_chunks)
 
    # ── Phase 2A: Neo4j graph expansion (optional — skipped if unavailable) ──
    retrieved_chunk_ids = [c["chunk_id"] for c in vector_chunks]

    graph_entities: list[dict] = []
    graph_paths:    list[str]  = []

    graph_used = False
    try:
        with driver.session() as session:
            result = session.run(
                f"""
                UNWIND $chunk_ids AS cid
                MATCH (chunk:Chunk {{chunk_id: cid}})
                MATCH (chunk)-[:MENTIONS]->(entity)
                OPTIONAL MATCH (entity)-[r]->(related)
                WHERE NOT related:Chunk AND NOT related:Document
                RETURN
                    chunk.chunk_id        AS chunk_id,
                    chunk.status          AS chunk_status,
                    labels(entity)[0]     AS entity_type,
                    entity.name           AS entity_name,
                    type(r)               AS rel_type,
                    labels(related)[0]    AS related_type,
                    related.name          AS related_name
                LIMIT {k * 10}
                """,
                chunk_ids=retrieved_chunk_ids,
            )

            for row in result.data():
                graph_entities.append({
                    "entity_type": row["entity_type"],
                    "entity_name": row["entity_name"],
                    "chunk_id":    row["chunk_id"],
                    "condition":   row["chunk_status"],
                })
                if row["rel_type"] and row["related_name"]:
                    graph_paths.append(
                        f"({row['entity_name']}:{row['entity_type']})"
                        f" -[{row['rel_type']}]-> "
                        f"({row['related_name']}:{row['related_type']})"
                    )
        graph_used = True
        print("[Neo4j] OK — graph expansion succeeded")
    except Exception as e:
        print(f"[Neo4j] UNAVAILABLE — {e.__class__.__name__}: {e}")

    # ── Phase 2B: Deduplicate graph results ───────────────────────────────
    graph_paths = list(dict.fromkeys(graph_paths))   # preserve order, dedup
 
    seen_entities: set[tuple] = set()
    unique_entities: list[dict] = []
    for e in graph_entities:
        key = (e["entity_type"], e["entity_name"])
        if key not in seen_entities:
            seen_entities.add(key)
            unique_entities.append(e)
    graph_entities = unique_entities
 
    # ── Phase 3: Build merged context string (fed to LLM) ─────────────────
    merged_context = _build_context(vector_chunks, graph_entities, graph_paths)
 
    return {
        "vector_chunks":   vector_chunks,
        "graph_entities":  graph_entities,
        "graph_paths":     graph_paths,
        "merged_context":  merged_context,
        "predicted_label": predicted_label,
        "confidence":      confidence,
        "graph_used":      graph_used,
    }
 
 
# ── Private helpers ────────────────────────────────────────────────────────
 
def _hybrid_vote(
    vector_chunks: list[dict],
    majority_weight: float = MAJORITY_WEIGHT,
) -> tuple[str, float, dict]:
    """
    Compute the hybrid majority + score-weighted vote.
 
    Returns:
        (predicted_label, confidence, combined_scores_dict)
    """
    if not vector_chunks:
        return "unknown", 0.0, {}
 
    n           = len(vector_chunks)
    total_score = sum(c["score"] for c in vector_chunks)
 
    vote_counts: dict[str, int]   = defaultdict(int)
    score_sums:  dict[str, float] = defaultdict(float)
 
    for chunk in vector_chunks:
        lbl = chunk["status"]
        vote_counts[lbl] += 1
        score_sums[lbl]  += chunk["score"]
 
    combined: dict[str, float] = {
        lbl: (
            majority_weight * (vote_counts[lbl] / n)
            + (1 - majority_weight) * (score_sums[lbl] / total_score)
        )
        for lbl in vote_counts
    }
 
    predicted_label = max(combined, key=combined.get)  # type: ignore[arg-type]
    return predicted_label, combined[predicted_label], combined
 
 
def _build_context(
    vector_chunks:  list[dict],
    graph_entities: list[dict],
    graph_paths:    list[str],
) -> str:
    """
    Format Qdrant + Neo4j results into the merged context block
    expected by graphrag_answer(). Mirrors notebook §14 format.
    """
    vector_context = "\n".join(
        f"[score={c['score']:.3f} | {c['status']}] {c['text'][:200]}"
        for c in vector_chunks[:5]
    )
    entity_context = "\n".join(
        f"  {e['entity_type']}: {e['entity_name']}"
        for e in graph_entities[:15]
    )
    path_context = "\n".join(graph_paths[:10])
 
    return (
        "=== SEMANTIC CHUNKS (Qdrant) ===\n"
        f"{vector_context}\n\n"
        "=== GRAPH ENTITIES (Neo4j) ===\n"
        f"{entity_context}\n\n"
        "=== GRAPH RELATIONSHIP PATHS (Neo4j) ===\n"
        f"{path_context}"
    )

