"""Plugin system base classes for search providers."""

from abc import ABC, abstractmethod
from typing import Any, Optional
from pydantic import BaseModel


class SearchRequest(BaseModel):
    """Standard search request model."""
    query: str
    max_results: int = 10
    filters: Optional[dict[str, Any]] = None
    user_id: Optional[str] = None


class SearchResult(BaseModel):
    """Standard search result model."""
    title: str
    url: Optional[str] = None
    snippet: str
    score: float
    metadata: Optional[dict[str, Any]] = None
    source: str


class SearchProvider(ABC):
    """Base class for search provider plugins."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the provider name."""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """Return the provider version."""
        pass
    
    @abstractmethod
    async def search(self, request: SearchRequest) -> list[SearchResult]:
        """Execute search and return results."""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the provider is available."""
        pass


class PluginManager:
    """Manages search provider plugins."""
    
    def __init__(self):
        self._providers: dict[str, SearchProvider] = {}
    
    def register(self, provider: SearchProvider) -> None:
        """Register a search provider."""
        self._providers[provider.name] = provider
    
    def unregister(self, name: str) -> None:
        """Unregister a search provider."""
        self._providers.pop(name, None)
    
    def get_provider(self, name: str) -> Optional[SearchProvider]:
        """Get a registered provider by name."""
        return self._providers.get(name)
    
    def list_providers(self) -> list[str]:
        """List all registered provider names."""
        return list(self._providers.keys())
    
    async def search(self, provider_name: str, request: SearchRequest) -> list[SearchResult]:
        """Search using a specific provider."""
        provider = self.get_provider(provider_name)
        if not provider:
            raise ValueError(f"Provider '{provider_name}' not found")
        return await provider.search(request)
    
    async def federated_search(self, request: SearchRequest, providers: Optional[list[str]] = None) -> dict[str, list[SearchResult]]:
        """Search across multiple providers."""
        if providers is None:
            providers = self.list_providers()
        
        results = {}
        for provider_name in providers:
            provider = self.get_provider(provider_name)
            if provider and await provider.health_check():
                try:
                    results[provider_name] = await provider.search(request)
                except Exception as e:
                    results[provider_name] = []
        
        return results


# Global plugin manager instance
plugin_manager = PluginManager()