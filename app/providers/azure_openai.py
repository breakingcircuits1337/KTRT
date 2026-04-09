from __future__ import annotations

import time

from openai import AsyncAzureOpenAI, RateLimitError, APIStatusError

from app.config import settings
from app.providers.base import LLMAdapter, ModelTrace
from app.utils.retry import TransientError, transient_retry


class AzureOpenAIAdapter(LLMAdapter):
    def __init__(self, deployment: str | None = None):
        self.model = deployment or settings.azure_openai_deployment
        self._client = AsyncAzureOpenAI(
            api_key=settings.azure_openai_api_key,
            azure_endpoint=settings.azure_openai_endpoint,
            api_version=settings.azure_openai_api_version,
        )

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
            role="azure_openai",
            model=self.model,
            prompt_tokens=usage.prompt_tokens if usage else 0,
            completion_tokens=usage.completion_tokens if usage else 0,
            latency_ms=latency_ms,
        )
        return text, trace
