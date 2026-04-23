"""
Qdrant vector search — returns the top-K nearest neighbours with their
disorder labels and similarity scores.
"""
from __future__ import annotations

from django.conf import settings

from .client import get_qdrant

_TOP_K = 5


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
