"""Google Gemini provider using the Generative Language REST API."""

import json
from collections.abc import AsyncIterator
from typing import Optional
from urllib.parse import quote

import httpx

from app.config import get_settings
from app.providers.ai.base import AIProvider

settings = get_settings()
DEFAULT_SYSTEM = "You are Nebula, a helpful and concise search assistant."
API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"


class GeminiProvider(AIProvider):
    name = "gemini"

    def _request_data(self, prompt: str, system: Optional[str]) -> dict:
        return {
            "systemInstruction": {
                "parts": [{"text": system or DEFAULT_SYSTEM}],
            },
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": 500, "temperature": 0.7},
        }

    def _headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": settings.gemini_api_key,
        }

    def _url(self, action: str) -> str:
        model = quote(settings.gemini_model, safe="")
        return f"{API_BASE_URL}/{model}:{action}"

    @staticmethod
    def _response_text(data: dict) -> Optional[str]:
        candidates = data.get("candidates", [])
        if not candidates:
            return None
        parts = candidates[0].get("content", {}).get("parts", [])
        text = "".join(part.get("text", "") for part in parts if isinstance(part, dict))
        return text or None

    async def complete(self, prompt: str, system: Optional[str] = None) -> Optional[str]:
        if not settings.gemini_api_key:
            return None
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                self._url("generateContent"),
                json=self._request_data(prompt, system),
                headers=self._headers(),
            )
            response.raise_for_status()
            text = self._response_text(response.json())
            return text.strip() if text else None

    async def stream(self, prompt: str, system: Optional[str] = None) -> AsyncIterator[str]:
        if not settings.gemini_api_key:
            return
        async with httpx.AsyncClient(timeout=60) as client:
            async with client.stream(
                "POST",
                self._url("streamGenerateContent"),
                params={"alt": "sse"},
                json=self._request_data(prompt, system),
                headers=self._headers(),
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    try:
                        data = json.loads(line[5:].strip())
                    except json.JSONDecodeError:
                        continue
                    text = self._response_text(data)
                    if text:
                        yield text
