"""Brave Search provider plugin."""

import os
from typing import Any, Optional

from app.plugins.base import SearchProvider, SearchRequest, SearchResult


class BraveSearchProvider(SearchProvider):
    """Brave Search API provider."""
    
    @property
    def name(self) -> str:
        return "brave"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    async def search(self, request: SearchRequest) -> list[SearchResult]:
        """Search using Brave Search API."""
        import httpx
        
        api_key = os.getenv("BRAVE_API_KEY")
        if not api_key:
            return []
        
        url = "https://api.search.brave.com/res/v1/web/search"
        headers = {
            "Accept": "application/json",
            "X-Subscription-Token": api_key,
        }
        params = {
            "q": request.query,
            "count": request.max_results,
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
        
        results = []
        for item in data.get("web", {}).get("results", []):
            results.append(SearchResult(
                title=item.get("title", ""),
                url=item.get("url", ""),
                snippet=item.get("description", ""),
                score=1.0,
                metadata={"source": "brave"},
                source="brave",
            ))
        
        return results
    
    async def health_check(self) -> bool:
        """Check if Brave API is available."""
        return bool(os.getenv("BRAVE_API_KEY"))