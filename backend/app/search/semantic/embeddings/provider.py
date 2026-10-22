"""
Abstract Embedding Provider Base Class

Defines the interface for all embedding providers.
Enables pluggable embedding generation from multiple AI providers.
"""

from abc import ABC, abstractmethod
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class EmbeddingProvider(ABC):
    """
    Abstract base class for embedding providers.
    
    All embedding provider implementations must inherit from this class
    and implement all abstract methods.
    """
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """
        Initialize embedding provider.
        
        Args:
            api_key: API key for the provider
            **kwargs: Additional configuration options
        """
        self.api_key = api_key
        self.config = kwargs
        self._model_name = kwargs.get('model_name', '')
        self._dimension = kwargs.get('dimension', 1536)
    
    @abstractmethod
    async def generate_embedding(self, text: str) -> list[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Input text
            
        Returns:
            Embedding vector (list of floats)
        """
        pass
    
    @abstractmethod
    async def generate_embeddings(self, texts: list[str], batch_size: int = 100) -> list[list[float]]:
        """
        Generate embeddings for multiple texts (batch processing).
        
        Args:
            texts: List of input texts
            batch_size: Number of texts per batch
            
        Returns:
            List of embedding vectors
        """
        pass
    
    @abstractmethod
    async def get_embedding_dimension(self) -> int:
        """
        Get the dimension of embeddings produced by this provider.
        
        Returns:
            Embedding dimension (e.g., 1536 for OpenAI)
        """
        pass
    
    @abstractmethod
    async def get_model_name(self) -> str:
        """
        Get the name of the embedding model.
        
        Returns:
            Model name string
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the embedding provider is healthy/available.
        
        Returns:
            True if healthy, False otherwise
        """
        pass
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        return False