"""AI provider interface."""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Optional


class AIProvider(ABC):
    name: str = "base"

    @abstractmethod
    async def complete(self, prompt: str, system: Optional[str] = None) -> Optional[str]:
        pass

    async def stream(self, prompt: str, system: Optional[str] = None) -> AsyncIterator[str]:
        answer = await self.complete(prompt, system)
        if answer:
            yield answer
