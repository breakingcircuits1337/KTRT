from __future__ import annotations

import time

from groq import AsyncGroq
from groq import RateLimitError, APIStatusError

from app.config import settings
from app.providers.base import LLMAdapter, ModelTrace
from app.utils.retry import TransientError, transient_retry


class GroqAdapter(LLMAdapter):
    def __init__(self, model: str = "llama-3.3-70b-versatile"):
        self.model = model
        self._client = AsyncGroq(api_key=settings.groq_api_key)

    @transient_retry(max_attempts=3)
    async def generate(
        self,
        system: str,
        user: str,
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> tuple[str, ModelTrace]:
        start = time.monotonic()
        try:
            resp = await self._client.chat.completions.create(
                model=self.model,
                temperature=temperature,
                max_tokens=max_tokens,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
        except RateLimitError as exc:
            raise TransientError(str(exc)) from exc
        except APIStatusError as exc:
            if exc.status_code >= 500:
                raise TransientError(str(exc)) from exc
            raise

        latency_ms = (time.monotonic() - start) * 1000
        text = resp.choices[0].message.content or ""
        usage = resp.usage
        trace = ModelTrace(
            role="groq",
            model=self.model,
            prompt_tokens=usage.prompt_tokens if usage else 0,
            completion_tokens=usage.completion_tokens if usage else 0,
            latency_ms=latency_ms,
        )
        return text, trace
