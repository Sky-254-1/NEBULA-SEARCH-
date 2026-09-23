"""
Vector Store Abstraction Layer

Provides a unified interface for multiple vector databases:
- PostgreSQL pgvector
- Qdrant
- Milvus
- Weaviate
- OpenSearch Vector
- Elasticsearch Vector

All vector stores implement the same interface for easy switching.
"""

from .abstract import VectorStore
from .pgvector_store import PGVectorStore
from .qdrant_store import QdrantStore
from .milvus_store import MilvusStore
from .elasticsearch_store import ElasticsearchVectorStore

__all__ = [
    "VectorStore",
    "PGVectorStore",
    "QdrantStore",
    "MilvusStore",
    "ElasticsearchVectorStore",
]