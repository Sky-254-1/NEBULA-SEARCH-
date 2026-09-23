"""Local GGUF model provider (offline inference stub).

Requires llama-cpp-python and a model path configured via GGUF_MODEL_PATH.
Falls back gracefully when not configured.
"""

import logging
from typing import Optional

from app.config import get_settings
from app.providers.ai.base import AIProvider

logger = logging.getLogger("nebula.ai.gguf")
settings = get_settings()


class GGUFProvider(AIProvider):
    name = "gguf"

    async def complete(self, prompt: str, system: Optional[str] = None) -> Optional[str]:
        model_path = getattr(settings, "gguf_model_path", "") or ""
        if not model_path:
            return None
        try:
            from llama_cpp import Llama

            llm = Llama(model_path=model_path, n_ctx=2048, verbose=False)
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})
            result = llm.create_chat_completion(messages=messages, max_tokens=500)
            content = result["choices"][0]["message"]["content"]
            return content.strip() if content else None
        except ImportError:
            logger.debug("llama-cpp-python not installed; GGUF provider unavailable")
            return None
        except Exception as exc:
            logger.debug("GGUF inference failed: %s", exc)
            return None
