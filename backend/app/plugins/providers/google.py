"""Google Custom Search API provider plugin."""

import os
from typing import Any, Optional

from app.plugins.base import SearchProvider, SearchRequest, SearchResult


class GoogleSearchProvider(SearchProvider):
    """Google Custom Search API provider."""
    
    @property
    def name(self) -> str:
        return "google"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    async def search(self, request: SearchRequest) -> list[SearchResult]:
        """Search using Google Custom Search API."""
        import httpx
        
        api_key = os.getenv("GOOGLE_API_KEY")
        cx = os.getenv("GOOGLE_SEARCH_CX")  # Custom Search Engine ID
        
        if not api_key or not cx:
            return []
        
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": api_key,
            "cx": cx,
            "q": request.query,
            "num": request.max_results,
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
        
        results = []
        for item in data.get("items", []):
            results.append(SearchResult(
                title=item.get("title", ""),
                url=item.get("link", ""),
                snippet=item.get("snippet", ""),
                score=1.0,
                metadata={"source": "google"},
                source="google",
            ))
        
        return results
    
    async def health_check(self) -> bool:
        """Check if Google API is available."""
        return bool(os.getenv("GOOGLE_API_KEY") and os.getenv("GOOGLE_SEARCH_CX"))