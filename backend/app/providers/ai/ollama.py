"""Ollama local model provider with streaming."""

import json
from collections.abc import AsyncIterator
from typing import Optional

import httpx

from app.config import get_settings
from app.providers.ai.base import AIProvider

settings = get_settings()
DEFAULT_SYSTEM = "You are Nebula, a helpful search assistant."


class OllamaProvider(AIProvider):
    name = "ollama"

    async def complete(self, prompt: str, system: Optional[str] = None) -> Optional[str]:
        url = f"{settings.ollama_url.rstrip('/')}/api/chat"
        payload = {
            "model": settings.ollama_model,
            "messages": [
                {"role": "system", "content": system or DEFAULT_SYSTEM},
                {"role": "user", "content": prompt},
            ],
            "stream": False,
        }
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()
            message = data.get("message", {})
            content = message.get("content", "").strip()
            return content or None
        except Exception:
            return None

    async def stream(self, prompt: str, system: Optional[str] = None) -> AsyncIterator[str]:
        url = f"{settings.ollama_url.rstrip('/')}/api/chat"
        payload = {
            "model": settings.ollama_model,
            "messages": [
                {"role": "system", "content": system or DEFAULT_SYSTEM},
                {"role": "user", "content": prompt},
            ],
            "stream": True,
        }
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                async with client.stream("POST", url, json=payload) as resp:
                    resp.raise_for_status()
                    async for line in resp.aiter_lines():
                        if not line:
                            continue
                        try:
                            data = json.loads(line)
                            content = data.get("message", {}).get("content")
                            if content:
                                yield content
                            if data.get("done"):
                                break
                        except json.JSONDecodeError:
                            continue
        except Exception:
            answer = await self.complete(prompt, system)
            if answer:
                yield answer
