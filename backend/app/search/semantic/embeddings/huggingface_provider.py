"""
HuggingFace Embedding Provider

Embedding generation using HuggingFace models.
Supports both API and local model inference.
"""

import logging
from typing import Optional
import httpx

from .provider import EmbeddingProvider

logger = logging.getLogger(__name__)


class HuggingFaceEmbeddingProvider(EmbeddingProvider):
    """
    HuggingFace embedding provider.
    
    Supports:
    - sentence-transformers models (via API)
    - Local model inference (optional)
    
    Popular models:
    - sentence-transformers/all-MiniLM-L6-v2 (384 dimensions)
    - sentence-transformers/all-mpnet-base-v2 (768 dimensions)
    - sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 (384 dimensions)
    
    Requires:
    - HuggingFace API key (for API usage)
    - transformers and torch (for local inference)
    """
    
    # Popular embedding models
    MODELS = {
        'sentence-transformers/all-MiniLM-L6-v2': {
            'dimension': 384,
            'max_tokens': 256,
        },
        'sentence-transformers/all-mpnet-base-v2': {
            'dimension': 768,
            'max_tokens': 384,
        },
        'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2': {
            'dimension': 384,
            'max_tokens': 128,
        },
        'sentence-transformers/paraphrase-multilingual-mpnet-base-v2': {
            'dimension': 768,
            'max_tokens': 384,
        },
    }
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """
        Initialize HuggingFace embedding provider.
        
        Args:
            api_key: HuggingFace API key
            **kwargs: Additional options (model_name, use_local, etc.)
        """
        super().__init__(api_key, **kwargs)
        
        # Set model
        self._model_name = kwargs.get('model_name', 'sentence-transformers/all-MiniLM-L6-v2')
        
        # Get dimension from model config
        if self._model_name in self.MODELS:
            self._dimension = self.MODELS[self._model_name]['dimension']
        
        # Configuration
        self.use_local = kwargs.get('use_local', False)
        self._api_url = "https://api-inference.huggingface.co/pipeline/feature-extraction/"
        self._client = httpx.AsyncClient(timeout=120.0)
        
        # Local model (optional)
        self._local_model = None
        if self.use_local:
            self._initialize_local_model()
    
    def _initialize_local_model(self):
        """Initialize local model for inference."""
        try:
            from sentence_transformers import SentenceTransformer
            self._local_model = SentenceTransformer(self._model_name)
            logger.info(f"Loaded local HuggingFace model: {self._model_name}")
        except ImportError:
            logger.warning("sentence-transformers not installed. Install with: pip install sentence-transformers")
            self.use_local = False
        except Exception as e:
            logger.error(f"Failed to load local model: {e}")
            self.use_local = False
    
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
            batch_size: Number of texts per batch
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        # Filter out empty texts
        valid_texts = [text for text in texts if text and text.strip()]
        if not valid_texts:
            return []
        
        # Use local model if available
        if self.use_local and self._local_model:
            return await self._generate_local(valid_texts)
        else:
            return await self._generate_api(valid_texts, batch_size)
    
    async def _generate_local(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings using local model.
        
        Args:
            texts: List of input texts
            
        Returns:
            List of embedding vectors
        """
        try:
            # Run in executor to avoid blocking
            import asyncio
            loop = asyncio.get_event_loop()
            
            embeddings = await loop.run_in_executor(
                None,
                lambda: self._local_model.encode(texts, convert_to_numpy=True).tolist()
            )
            
            return embeddings
        except Exception as e:
            logger.error(f"Local embedding generation failed: {e}")
            return [[] for _ in texts]
    
    async def _generate_api(self, texts: list[str], batch_size: int = 100) -> list[list[float]]:
        """
        Generate embeddings using HuggingFace API.
        
        Args:
            texts: List of input texts
            batch_size: Number of texts per batch
            
        Returns:
            List of embedding vectors
        """
        all_embeddings = []
        
        # Process in batches
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            try:
                batch_embeddings = await self._generate_api_batch(batch)
                all_embeddings.extend(batch_embeddings)
            except Exception as e:
                logger.error(f"Failed to generate embeddings for batch {i}: {e}")
                # Add empty embeddings for failed batch
                all_embeddings.extend([[] for _ in batch])
        
        return all_embeddings
    
    async def _generate_api_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for a batch using API.
        
        Args:
            texts: List of texts
            
        Returns:
            List of embedding vectors
        """
        # Prepare request
        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }
        
        # Use model-specific API endpoint
        url = f"{self._api_url}{self._model_name}"
        
        # Make API request
        response = await self._client.post(
            url,
            headers=headers,
            json={"inputs": texts},
        )
        
        response.raise_for_status()
        data = response.json()
        
        # HuggingFace returns either a list or nested list
        if isinstance(data, list):
            # Single embedding or list of embeddings
            if len(texts) == 1:
                return [data]
            else:
                return data
        else:
            # Unexpected format
            logger.warning(f"Unexpected API response format: {type(data)}")
            return [[] for _ in texts]
    
    async def get_embedding_dimension(self) -> int:
        """Get embedding dimension."""
        return self._dimension
    
    async def get_model_name(self) -> str:
        """Get model name."""
        return self._model_name
    
    async def health_check(self) -> bool:
        """Check if HuggingFace API is available."""
        try:
            # Try to generate a simple embedding
            await self.generate_embedding("test")
            return True
        except Exception as e:
            logger.error(f"HuggingFace health check failed: {e}")
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