"""DuckDuckGo Search provider plugin."""

import os
from typing import Any, Optional

from app.plugins.base import SearchProvider, SearchRequest, SearchResult


class DuckDuckGoSearchProvider(SearchProvider):
    """DuckDuckGo Search provider plugin."""
    
    @property
    def name(self) -> str:
        return "duckduckgo"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    async def search(self, request: SearchRequest) -> list[SearchResult]:
        """Search using DuckDuckGo Instant Answer API."""
        import httpx
        
        url = "https://api.duckduckgo.com/"
        params = {
            "q": request.query,
            "format": "json",
            "no_html": 1,
            "skip_disambig": 1,
        }
        
        results = []
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
        
        # Extract abstract/answer
        if data.get("Abstract"):
            results.append(SearchResult(
                title=data.get("Heading", request.query),
                url=data.get("AbstractURL", ""),
                snippet=data.get("Abstract", ""),
                score=1.0,
                metadata={"source": "duckduckgo", "type": "abstract"},
                source="duckduckgo",
            ))
        
        # Extract related topics
        for topic in data.get("RelatedTopics", [])[:request.max_results]:
            if isinstance(topic, dict) and "Text" in topic:
                results.append(SearchResult(
                    title=topic.get("Text", "").split(" - ")[0],
                    url=topic.get("FirstURL", ""),
                    snippet=topic.get("Text", ""),
                    score=0.8,
                    metadata={"source": "duckduckgo", "type": "related"},
                    source="duckduckgo",
                ))
        
        return results
    
    async def health_check(self) -> bool:
        """Check if DuckDuckGo API is available."""
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get("https://api.duckduckgo.com/", params={"q": "test", "format": "json"}, timeout=5.0)
                return response.status_code == 200
        except Exception:
            return False