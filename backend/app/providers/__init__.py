"""AI provider abstractions."""

from app.providers.ai.base import AIProvider
from app.providers.ai.duckduckgo import DuckDuckGoProvider
from app.providers.ai.ollama import OllamaProvider
from app.providers.ai.openai import OpenAIProvider
from app.providers.ai.router import AIProviderRouter

__all__ = [
    "AIProvider",
    "AIProviderRouter",
    "DuckDuckGoProvider",
    "OllamaProvider",
    "OpenAIProvider",
]
