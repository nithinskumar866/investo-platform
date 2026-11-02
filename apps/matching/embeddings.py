"""Semantic similarity via a local Ollama embedding model.

Everything is optional: if Ollama is off, callers get None and fall back to
keyword matching. Embeddings are cached, so scoring many pairs stays cheap.
"""
import hashlib
import json
import logging
import math
import urllib.request

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

CACHE_TTL = 60 * 60 * 24 * 30
OFFLINE_KEY = "embeddings:offline"
# Cosine similarity for this kind of text falls roughly in this band.
SIMILARITY_FLOOR = 0.35
SIMILARITY_CEILING = 0.75


def _embed(text: str):
    key = f"embeddings:{settings.EMBEDDING_MODEL}:{hashlib.sha256(text.encode()).hexdigest()}"
    vector = cache.get(key)
    if vector is not None:
        return vector
    request = urllib.request.Request(
        f"{settings.OLLAMA_URL}/api/embed",
        data=json.dumps({"model": settings.EMBEDDING_MODEL, "input": text[:4000]}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        vector = json.loads(response.read())["embeddings"][0]
    cache.set(key, vector, CACHE_TTL)
    return vector


def similarity_score(text_a: str, text_b: str):
    """Return 0-100 for how close two texts are in meaning, or None if unavailable."""
    if not settings.MATCH_EMBEDDINGS_ENABLED or not text_a.strip() or not text_b.strip():
        return None
    if cache.get(OFFLINE_KEY):
        return None
    try:
        a, b = _embed(text_a), _embed(text_b)
    except (OSError, ValueError, KeyError, IndexError) as exc:
        logger.warning(f"Embeddings unavailable, using keyword matching: {exc}")
        cache.set(OFFLINE_KEY, True, 60)
        return None
    norm = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    if not norm:
        return None
    cosine = sum(x * y for x, y in zip(a, b)) / norm
    scaled = (cosine - SIMILARITY_FLOOR) / (SIMILARITY_CEILING - SIMILARITY_FLOOR)
    return max(0.0, min(100.0, scaled * 100))
