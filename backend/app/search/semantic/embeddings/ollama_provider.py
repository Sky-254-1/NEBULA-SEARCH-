"""
Ollama Embedding Provider

Embedding generation using Ollama local models.
Provides privacy-first, offline-capable embedding generation.
"""

import logging
from typing import Optional
import httpx

from .provider import EmbeddingProvider

logger = logging.getLogger(__name__)


class OllamaEmbeddingProvider(EmbeddingProvider):
    """
    Ollama embedding provider for local model inference.
    
    Supports:
    - llama2-embed (4096 dimensions)
    - nomic-embed-text (768 dimensions)
    - all-minilm (384 dimensions)
    - Any Ollama-compatible embedding model
    
    Requires:
    - Ollama server running locally (default: http://localhost:11434)
    - Model pulled via `ollama pull <model_name>`
    """
    
    # Popular Ollama embedding models
    MODELS = {
        'llama2-embed': {
            'dimension': 4096,
            'max_tokens': 4096,
        },
        'nomic-embed-text': {
            'dimension': 768,
            'max_tokens': 8192,
        },
        'all-minilm': {
            'dimension': 384,
            'max_tokens': 256,
        },
    }
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """
        Initialize Ollama embedding provider.
        
        Args:
            api_key: Not required for Ollama (local), but kept for interface compatibility
            **kwargs: Additional options (model_name, base_url, etc.)
        """
        super().__init__(api_key, **kwargs)
        
        # Set model
        self._model_name = kwargs.get('model_name', 'nomic-embed-text')
        
        # Get dimension from model config
        if self._model_name in self.MODELS:
            self._dimension = self.MODELS[self._model_name]['dimension']
        
        # Ollama server URL
        self._base_url = kwargs.get('base_url', 'http://localhost:11434')
        self._api_url = f"{self._base_url}/api/embeddings"
        self._client = httpx.AsyncClient(timeout=120.0)
    
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
            batch_size: Number of texts per batch (Ollama processes one at a time)
            
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
        
        # Ollama processes one at a time (no native batching)
        for text in valid_texts:
            try:
                embedding = await self._generate_single(text)
                all_embeddings.append(embedding)
            except Exception as e:
                logger.error(f"Failed to generate embedding: {e}")
                all_embeddings.append([])
        
        return all_embeddings
    
    async def _generate_single(self, text: str) -> list[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Input text
            
        Returns:
            Embedding vector
        """
        # Prepare request
        payload = {
            "model": self._model_name,
            "prompt": text,
        }
        
        # Make API request
        response = await self._client.post(
            self._api_url,
            json=payload,
        )
        
        response.raise_for_status()
        data = response.json()
        
        # Extract embedding
        embedding = data.get('embedding', [])
        
        return embedding
    
    async def get_embedding_dimension(self) -> int:
        """Get embedding dimension."""
        return self._dimension
    
    async def get_model_name(self) -> str:
        """Get model name."""
        return self._model_name
    
    async def health_check(self) -> bool:
        """Check if Ollama server is available."""
        try:
            # Try to connect to Ollama server
            response = await self._client.get(f"{self._base_url}/api/tags")
            response.raise_for_status()
            
            # Check if model is available
            data = response.json()
            models = [model['name'] for model in data.get('models', [])]
            
            if self._model_name not in models:
                logger.warning(f"Model {self._model_name} not found in Ollama. Available: {models}")
                return False
            
            return True
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return False
    
    async def list_available_models(self) -> list[str]:
        """
        List available models in Ollama.
        
        Returns:
            List of model names
        """
        try:
            response = await self._client.get(f"{self._base_url}/api/tags")
            response.raise_for_status()
            
            data = response.json()
            models = [model['name'] for model in data.get('models', [])]
            
            return models
        except Exception as e:
            logger.error(f"Failed to list Ollama models: {e}")
            return []
    
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