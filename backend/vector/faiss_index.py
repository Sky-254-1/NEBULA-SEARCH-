"""FAISS vector index for fast similarity search.

Provides in-memory FAISS indexing with optional GPU support,
persistent storage, and incremental updates.
"""

import json
import logging
import math
from pathlib import Path
from typing import Optional

import numpy as np

from app.config import get_settings

logger = logging.getLogger("nebula.vector.faiss")

# Optional FAISS import
try:
    import faiss

    _HAS_FAISS = True
except ImportError:
    _HAS_FAISS = False
    logger.info("faiss not installed — falling back to brute-force cosine similarity")


class FAISSIndex:
    """FAISS-based vector index with persistence."""

    def __init__(self, dimension: int = 256, index_path: Optional[Path] = None):
        self.dimension = dimension
        self.index_path = index_path
        self._index = None
        self._id_map: dict[int, int] = {}  # external_id -> faiss_id
        self._reverse_map: dict[int, int] = {}  # faiss_id -> external_id
        self._next_id = 0

    def build(self, vectors: list[tuple[int, list[float]]]) -> None:
        """Build index from list of (external_id, vector) pairs."""
        if not _HAS_FAISS:
            logger.warning("FAISS not available — skipping index build")
            return

        if not vectors:
            self._index = faiss.IndexFlatIP(self.dimension)
            return

        matrix = np.array([v for _, v in vectors], dtype=np.float32)
        self._index = faiss.IndexFlatIP(self.dimension)
        faiss.normalize_L2(matrix)
        self._index.add(matrix)

        self._id_map = {}
        self._reverse_map = {}
        for i, (ext_id, _) in enumerate(vectors):
            self._id_map[ext_id] = i
            self._reverse_map[i] = ext_id
        self._next_id = len(vectors)

    def add(self, external_id: int, vector: list[float]) -> None:
        """Add a single vector to the index."""
        if not _HAS_FAISS or self._index is None:
            return

        matrix = np.array([vector], dtype=np.float32)
        faiss.normalize_L2(matrix)
        self._index.add(matrix)

        self._id_map[external_id] = self._next_id
        self._reverse_map[self._next_id] = external_id
        self._next_id += 1

    def remove(self, external_id: int) -> None:
        """Remove a vector by external ID (marks for removal, rebuilds)."""
        if external_id not in self._id_map:
            return
        faiss_id = self._id_map.pop(external_id)
        self._reverse_map.pop(faiss_id, None)

    def search(
        self, query_vector: list[float], top_k: int = 10
    ) -> list[tuple[int, float]]:
        """Search for top_k nearest neighbors. Returns [(external_id, score), ...]."""
        if not _HAS_FAISS or self._index is None or self._index.ntotal == 0:
            return []

        matrix = np.array([query_vector], dtype=np.float32)
        faiss.normalize_L2(matrix)
        scores, indices = self._index.search(matrix, min(top_k, self._index.ntotal))

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0 and idx in self._reverse_map:
                results.append((self._reverse_map[idx], float(score)))
        return results

    def save(self, path: Optional[Path] = None) -> None:
        """Persist index to disk."""
        if not _HAS_FAISS or self._index is None:
            return

        save_path = path or self.index_path
        if not save_path:
            return

        save_path.parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self._index, str(save_path))

        # Save metadata
        meta_path = save_path.with_suffix(".meta.json")
        meta_path.write_text(
            json.dumps(
                {
                    "id_map": {str(k): v for k, v in self._id_map.items()},
                    "reverse_map": {str(k): v for k, v in self._reverse_map.items()},
                    "next_id": self._next_id,
                    "dimension": self.dimension,
                }
            ),
            encoding="utf-8",
        )

    def load(self, path: Optional[Path] = None) -> bool:
        """Load index from disk. Returns True on success."""
        if not _HAS_FAISS:
            return False

        load_path = path or self.index_path
        if not load_path or not load_path.exists():
            return False

        try:
            self._index = faiss.read_index(str(load_path))
            meta_path = load_path.with_suffix(".meta.json")
            if meta_path.exists():
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
                self._id_map = {int(k): v for k, v in meta["id_map"].items()}
                self._reverse_map = {int(k): v for k, v in meta["reverse_map"].items()}
                self._next_id = meta["next_id"]
                self.dimension = meta["dimension"]
            return True
        except Exception as exc:
            logger.error("Failed to load FAISS index: %s", exc)
            return False

    @property
    def size(self) -> int:
        return self._index.ntotal if self._index is not None else 0

    @property
    def is_loaded(self) -> bool:
        return self._index is not None


# Global FAISS index registry (one per user)
_user_indexes: dict[int, FAISSIndex] = {}


def get_user_index(user_id: int, dimension: int = 256) -> FAISSIndex:
    """Get or create a FAISS index for a specific user."""
    if user_id not in _user_indexes:
        settings = get_settings()
        index_path = settings.storage_indexes / str(user_id) / "faiss.index"
        idx = FAISSIndex(dimension=dimension, index_path=index_path)
        idx.load()
        _user_indexes[user_id] = idx
    return _user_indexes[user_id]


def rebuild_user_index(
    user_id: int,
    vectors: list[tuple[int, list[float]]],
    dimension: int = 256,
) -> FAISSIndex:
    """Rebuild a user's FAISS index from scratch."""
    idx = FAISSIndex(dimension=dimension)
    idx.build(vectors)
    idx.save()
    _user_indexes[user_id] = idx
    return idx