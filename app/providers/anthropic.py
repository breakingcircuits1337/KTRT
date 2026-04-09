from __future__ import annotations

import time

import anthropic

from app.config import settings
from app.providers.base import LLMAdapter, ModelTrace
from app.utils.retry import TransientError, transient_retry


class AnthropicAdapter(LLMAdapter):
    def __init__(self, model: str = "claude-sonnet-4-6"):
        self.model = model
        self._client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

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
            resp = await self._client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
        except anthropic.RateLimitError as exc:
            raise TransientError(str(exc)) from exc
        except anthropic.APIStatusError as exc:
            if exc.status_code >= 500:
                raise TransientError(str(exc)) from exc
            raise

        latency_ms = (time.monotonic() - start) * 1000
        text = resp.content[0].text if resp.content else ""
        trace = ModelTrace(
            role="anthropic",
            model=self.model,
            prompt_tokens=resp.usage.input_tokens,
            completion_tokens=resp.usage.output_tokens,
            latency_ms=latency_ms,
        )
        return text, trace
