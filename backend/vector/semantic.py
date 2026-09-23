"""Semantic embeddings using sentence-transformers.

Provides high-quality embeddings via sentence-transformers models
with automatic model downloading, caching, and batching.
"""

import logging
import numpy as np
from typing import Optional

logger = logging.getLogger("nebula.vector.semantic")

# Optional sentence-transformers import
try:
    from sentence_transformers import SentenceTransformer

    _HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    _HAS_SENTENCE_TRANSFORMERS = False
    logger.info("sentence-transformers not installed — using hash-based embeddings")


# Global model cache
_model_cache: dict[str, "SentenceTransformer"] = {}


def get_model(model_name: str = "all-MiniLM-L6-v2") -> Optional["SentenceTransformer"]:
    """Get or load a sentence-transformers model (cached)."""
    if not _HAS_SENTENCE_TRANSFORMERS:
        return None

    if model_name not in _model_cache:
        try:
            logger.info("Loading sentence-transformers model: %s", model_name)
            model = SentenceTransformer(model_name)
            _model_cache[model_name] = model
            logger.info("Model loaded: %s (dim=%d)", model_name, model.get_sentence_embedding_dimension())
        except Exception as exc:
            logger.error("Failed to load model %s: %s", model_name, exc)
            return None

    return _model_cache[model_name]


def get_embedding_dimension(model_name: str = "all-MiniLM-L6-v2") -> int:
    """Get the embedding dimension for a model."""
    model = get_model(model_name)
    if model is None:
        return 384  # default for all-MiniLM-L6-v2
    return model.get_sentence_embedding_dimension()


async def embed_semantic(
    text: str,
    model_name: str = "all-MiniLM-L6-v2",
    normalize: bool = True,
) -> tuple[list[float], str, int]:
    """Generate semantic embedding for a single text.

    Returns:
        Tuple of (embedding_vector, model_name, dimension)
    """
    model = get_model(model_name)
    if model is None:
        # Fallback to hash-based embedding
        from vector.embeddings import _hash_embed
        vec = _hash_embed(text, dimensions=384)
        return vec, "local-hash-fallback", 384

    embedding = model.encode(text, normalize_embeddings=normalize)
    return embedding.tolist(), model_name, len(embedding)


async def embed_batch(
    texts: list[str],
    model_name: str = "all-MiniLM-L6-v2",
    batch_size: int = 32,
    normalize: bool = True,
    show_progress: bool = False,
) -> list[tuple[list[float], str, int]]:
    """Generate semantic embeddings for a batch of texts.

    More efficient than calling embed_semantic repeatedly.
    """
    model = get_model(model_name)
    if model is None:
        from vector.embeddings import _hash_embed
        return [(_hash_embed(t, dimensions=384), "local-hash-fallback", 384) for t in texts]

    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        normalize_embeddings=normalize,
        show_progress_bar=show_progress,
    )

    results = []
    for emb in embeddings:
        results.append((emb.tolist(), model_name, len(emb)))
    return results


def compute_similarity(embedding_a: list[float], embedding_b: list[float]) -> float:
    """Compute cosine similarity between two embeddings."""
    a = np.array(embedding_a, dtype=np.float32)
    b = np.array(embedding_b, dtype=np.float32)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))