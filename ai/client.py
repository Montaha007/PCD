"""
Qdrant connection singleton.

Reads QDRANT_URL and QDRANT_API_KEY from Django settings.
The client is created once and reused for the lifetime of the process.
"""
from __future__ import annotations

from qdrant_client import QdrantClient

_client: QdrantClient | None = None


def get_qdrant() -> QdrantClient:
    global _client
    if _client is None:
        from django.conf import settings
        _client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY,
        )
    return _client
