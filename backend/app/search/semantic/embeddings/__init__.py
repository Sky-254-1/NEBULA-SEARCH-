"""
Embedding Providers

Pluggable embedding generation system supporting multiple providers:
- OpenAI
- Cohere
- HuggingFace
- Ollama (local)

All providers implement the same interface for easy switching.
"""

from .provider import EmbeddingProvider
from .openai_provider import OpenAIEmbeddingProvider
from .cohere_provider import CohereEmbeddingProvider
from .huggingface_provider import HuggingFaceEmbeddingProvider
from .ollama_provider import OllamaEmbeddingProvider

__all__ = [
    "EmbeddingProvider",
    "OpenAIEmbeddingProvider",
    "CohereEmbeddingProvider",
    "HuggingFaceEmbeddingProvider",
    "OllamaEmbeddingProvider",
]