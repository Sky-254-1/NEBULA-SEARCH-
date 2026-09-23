"""
Cohere Embedding Provider

Embedding generation using Cohere's embedding models.
"""

import logging
from typing import Optional
import httpx

from .provider import EmbeddingProvider

logger = logging.getLogger(__name__)


class CohereEmbeddingProvider(EmbeddingProvider):
    """
    Cohere embedding provider.
    
    Supports:
    - embed-english-v3.0 (1024 dimensions)
    - embed-multilingual-v3.0 (1024 dimensions)
    - embed-english-light-v3.0 (384 dimensions)
    - embed-multilingual-light-v3.0 (384 dimensions)
    
    Requires:
    - Cohere API key
    """
    
    # Model configurations
    MODELS = {
        'embed-english-v3.0': {
            'dimension': 1024,
            'max_tokens': 512,
        },
        'embed-multilingual-v3.0': {
            'dimension': 1024,
            'max_tokens': 512,
        },
        'embed-english-light-v3.0': {
            'dimension': 384,
            'max_tokens': 512,
        },
        'embed-multilingual-light-v3.0': {
            'dimension': 384,
            'max_tokens': 512,
        },
    }
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """
        Initialize Cohere embedding provider.
        
        Args:
            api_key: Cohere API key
            **kwargs: Additional options (model_name, etc.)
        """
        super().__init__(api_key, **kwargs)
        
        # Set model
        self._model_name = kwargs.get('model_name', 'embed-english-v3.0')
        
        # Get dimension from model config
        if self._model_name in self.MODELS:
            self._dimension = self.MODELS[self._model_name]['dimension']
        
        # API endpoint
        self._api_url = "https://api.cohere.ai/v1/embed"
        self._client = httpx.AsyncClient(timeout=60.0)
    
    async def generate_embedding(self, text: str) -> list[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Input text
            
        Returns:
            Embedding vector
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        embeddings = await self.generate_embeddings([text])
        return embeddings[0] if embeddings else []
    
    async def generate_embeddings(self, texts: list[str], batch_size: int = 100) -> list[list[float]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of input texts
            batch_size: Number of texts per batch (Cohere allows up to 96)
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        # Filter out empty texts
        valid_texts = [text for text in texts if text and text.strip()]
        if not valid_texts:
            return []
        
        all_embeddings = []
        
        # Process in batches
        for i in range(0, len(valid_texts), batch_size):
            batch = valid_texts[i:i + batch_size]
            
            try:
                batch_embeddings = await self._generate_batch(batch)
                all_embeddings.extend(batch_embeddings)
            except Exception as e:
                logger.error(f"Failed to generate embeddings for batch {i}: {e}")
                # Add empty embeddings for failed batch
                all_embeddings.extend([[] for _ in batch])
        
        return all_embeddings
    
    async def _generate_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for a batch of texts.
        
        Args:
            texts: List of texts (max 96 for Cohere)
            
        Returns:
            List of embedding vectors
        """
        # Prepare request
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "texts": texts,
            "model": self._model_name,
            "input_type": "search_document",  # For document embeddings
        }
        
        # Make API request
        response = await self._client.post(
            self._api_url,
            headers=headers,
            json=payload,
        )
        
        response.raise_for_status()
        data = response.json()
        
        # Extract embeddings
        embeddings = [embedding for embedding in data.get('embeddings', [])]
        
        return embeddings
    
    async def get_embedding_dimension(self) -> int:
        """Get embedding dimension."""
        return self._dimension
    
    async def get_model_name(self) -> str:
        """Get model name."""
        return self._model_name
    
    async def health_check(self) -> bool:
        """Check if Cohere API is available."""
        try:
            # Try to generate a simple embedding
            await self.generate_embedding("test")
            return True
        except Exception as e:
            logger.error(f"Cohere health check failed: {e}")
            return False
    
    async def close(self):
        """Close HTTP client."""
        await self._client.aclose()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
        return False