"""
Semantic Search Module

Provides semantic search capabilities using vector embeddings:
- Embedding generation (multiple providers)
- Vector storage (multiple backends)
- Semantic search and reranking
- Document indexing with chunking
"""

from .engine import SemanticEngine
from .indexer import DocumentIndexer

__all__ = [
    "SemanticEngine",
    "DocumentIndexer",
]