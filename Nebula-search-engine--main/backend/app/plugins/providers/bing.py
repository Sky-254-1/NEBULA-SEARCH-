"""Bing Web Search API provider plugin."""

import os
from typing import Any, Optional

from app.plugins.base import SearchProvider, SearchRequest, SearchResult


class BingSearchProvider(SearchProvider):
    """Bing Web Search API provider."""
    
    @property
    def name(self) -> str:
        return "bing"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    async def search(self, request: SearchRequest) -> list[SearchResult]:
        """Search using Bing Web Search API."""
        import httpx
        
        api_key = os.getenv("BING_API_KEY")
        if not api_key:
            return []
        
        url = "https://api.bing.microsoft.com/v7.0/search"
        headers = {
            "Ocp-Apim-Subscription-Key": api_key,
        }
        params = {
            "q": request.query,
            "count": request.max_results,
            "textDecorations": False,
            "textFormat": "raw",
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
        
        results = []
        for item in data.get("webPages", {}).get("value", []):
            results.append(SearchResult(
                title=item.get("name", ""),
                url=item.get("url", ""),
                snippet=item.get("snippet", ""),
                score=1.0,
                metadata={"source": "bing"},
                source="bing",
            ))
        
        return results
    
    async def health_check(self) -> bool:
        """Check if Bing API is available."""
        return bool(os.getenv("BING_API_KEY"))