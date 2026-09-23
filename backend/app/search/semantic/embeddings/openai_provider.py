"""
OpenAI Embedding Provider

Embedding generation using OpenAI's embedding models.
"""

import logging
from typing import Optional
import httpx

from .provider import EmbeddingProvider

logger = logging.getLogger(__name__)


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """
    OpenAI embedding provider.
    
    Supports:
    - text-embedding-3-small (1536 dimensions)
    - text-embedding-3-large (3072 dimensions)
    - text-embedding-ada-002 (1536 dimensions)
    
    Requires:
    - OpenAI API key
    - openai package (optional, uses httpx directly)
    """
    
    # Model configurations
    MODELS = {
        'text-embedding-3-small': {
            'dimension': 1536,
            'max_tokens': 8191,
        },
        'text-embedding-3-large': {
            'dimension': 3072,
            'max_tokens': 8191,
        },
        'text-embedding-ada-002': {
            'dimension': 1536,
            'max_tokens': 8191,
        },
    }
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """
        Initialize OpenAI embedding provider.
        
        Args:
            api_key: OpenAI API key
            **kwargs: Additional options (model_name, etc.)
        """
        super().__init__(api_key, **kwargs)
        
        # Set model
        self._model_name = kwargs.get('model_name', 'text-embedding-3-small')
        
        # Get dimension from model config
        if self._model_name in self.MODELS:
            self._dimension = self.MODELS[self._model_name]['dimension']
        
        # API endpoint
        self._api_url = "https://api.openai.com/v1/embeddings"
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
            batch_size: Number of texts per batch (OpenAI allows up to 2048)
            
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
            texts: List of texts (max 2048 for OpenAI)
            
        Returns:
            List of embedding vectors
        """
        # Prepare request
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "input": texts,
            "model": self._model_name,
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
        embeddings = []
        for item in sorted(data.get('data', []), key=lambda x: x['index']):
            embeddings.append(item.get('embedding', []))
        
        return embeddings
    
    async def get_embedding_dimension(self) -> int:
        """Get embedding dimension."""
        return self._dimension
    
    async def get_model_name(self) -> str:
        """Get model name."""
        return self._model_name
    
    async def health_check(self) -> bool:
        """Check if OpenAI API is available."""
        try:
            # Try to generate a simple embedding
            await self.generate_embedding("test")
            return True
        except Exception as e:
            logger.error(f"OpenAI health check failed: {e}")
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