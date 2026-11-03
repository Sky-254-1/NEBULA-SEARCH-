"""Route prompts to the best available AI provider."""

import logging
from collections.abc import AsyncIterator
from typing import Optional

from app.config import get_settings
from app.providers.ai.duckduckgo import DuckDuckGoProvider
from app.providers.ai.gemini import GeminiProvider
from app.providers.ai.gguf import GGUFProvider
from app.providers.ai.ollama import OllamaProvider
from app.providers.ai.openai import OpenAIProvider

logger = logging.getLogger("nebula.ai.router")
settings = get_settings()


class AIProviderRouter:
    def __init__(self) -> None:
        self._providers = {
            "openai": OpenAIProvider(),
            "gemini": GeminiProvider(),
            "ollama": OllamaProvider(),
            "gguf": GGUFProvider(),
            "duckduckgo": DuckDuckGoProvider(),
        }

    def _ordered_providers(self) -> list[str]:
        if settings.ai_provider == "openai":
            return ["openai", "gemini", "ollama", "gguf", "duckduckgo"]
        if settings.ai_provider == "gemini":
            return ["gemini", "openai", "ollama", "gguf", "duckduckgo"]
        if settings.ai_provider == "ollama":
            return ["ollama", "gguf", "openai", "gemini", "duckduckgo"]
        if settings.ai_provider == "gguf":
            return ["gguf", "ollama", "openai", "gemini", "duckduckgo"]
        if settings.ai_provider == "duckduckgo":
            return ["duckduckgo", "openai", "gemini", "ollama", "gguf"]
        order = []
        if settings.openai_api_key:
            order.append("openai")
        if settings.gemini_api_key:
            order.append("gemini")
        order.extend(["ollama", "gguf", "duckduckgo"])
        return order

    async def complete(self, prompt: str, system: Optional[str] = None) -> tuple[Optional[str], str]:
        for name in self._ordered_providers():
            provider = self._providers[name]
            try:
                answer = await provider.complete(prompt, system)
                if answer:
                    return answer, name
            except Exception as exc:
                logger.debug("Provider %s failed: %s", name, exc)
        return None, "none"

    async def stream(self, prompt: str, system: Optional[str] = None) -> AsyncIterator[str]:
        for name in self._ordered_providers():
            provider = self._providers[name]
            try:
                emitted = False
                async for chunk in provider.stream(prompt, system):
                    emitted = True
                    yield chunk
                if emitted:
                    return
            except Exception as exc:
                logger.debug("Provider %s stream failed: %s", name, exc)
        answer, _ = await self.complete(prompt, system)
        if answer:
            yield answer
