"""DuckDuckGo instant answer fallback provider."""

from typing import Optional
from urllib.parse import quote

import httpx

from app.providers.ai.base import AIProvider


class DuckDuckGoProvider(AIProvider):
    name = "duckduckgo"

    async def complete(self, prompt: str, system: Optional[str] = None) -> Optional[str]:
        url = f"https://api.duckduckgo.com/?q={quote(prompt)}&format=json&no_redirect=1&t=nebula"
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
        return data.get("AbstractText") or data.get("Answer") or None
