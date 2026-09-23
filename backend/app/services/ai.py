"""AI completion and synthesis services."""

import logging
from collections.abc import AsyncIterator

from app.models.schemas import SynthesizeResponse
from app.providers.ai.router import AIProviderRouter
from app.services.cache import cache_service

logger = logging.getLogger("nebula.ai")
router = AIProviderRouter()

SYSTEM_PROMPT = (
    "You are Nebula, a helpful and concise search assistant. "
    "Provide clear, accurate, and brief answers. "
    "If you're unsure, say so. Do not make up facts."
)


async def get_ai_answer(prompt: str, use_cache: bool = True) -> tuple[str | None, str]:
    cache_key = f"ai:{prompt[:200]}"
    if use_cache:
        cached = await cache_service.get(cache_key)
        if cached:
            return cached.get("answer"), cached.get("provider", "cache")

    answer, provider = await router.complete(prompt, SYSTEM_PROMPT)
    if answer and use_cache:
        await cache_service.set(cache_key, {"answer": answer, "provider": provider})
    return answer, provider


async def stream_ai_answer(prompt: str) -> AsyncIterator[str]:
    async for chunk in router.stream(prompt, SYSTEM_PROMPT):
        yield chunk


async def synthesize_snippets(query: str, snippets: list[str]) -> SynthesizeResponse:
    """Synthesize search snippets into a coherent answer with citations."""
    combined = "\n".join(f"- [{i+1}] {snippet}" for i, snippet in enumerate(snippets[:10]))
    prompt = (
        f'The user searched for: "{query}"\n\n'
        f"Here are the top search result snippets:\n{combined}\n\n"
        "Synthesize these into a clear, concise summary paragraph (3-5 sentences). "
        "Reference sources using [1], [2], etc. notation matching the snippet numbers. "
        "Do not add information not present in the snippets."
    )
    answer, _provider = await router.complete(prompt, SYSTEM_PROMPT)
    
    # Create citations for each snippet
    sources = [snippet[:200] + "..." if len(snippet) > 200 else snippet for snippet in snippets[:10]]
    
    if answer:
        return SynthesizeResponse(synthesis=answer, sources=sources)

    # Fallback: simple concatenation with citations
    transitions = [
        "According to search results [1], ",
        "Additionally [2], ",
        "Furthermore [3], ",
        "It is also noted that [4], ",
        "Moreover [5], ",
    ]
    parts = []
    for index, snippet in enumerate(snippets[:5]):
        prefix = transitions[index] if index < len(transitions) else f"[{index+1}] "
        parts.append(f"{prefix}{snippet.strip().rstrip('.')}.")
    return SynthesizeResponse(synthesis=" ".join(parts), sources=sources)
