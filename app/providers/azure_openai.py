from __future__ import annotations

import time

from openai import AsyncOpenAI, RateLimitError, APIStatusError

from app.config import settings
from app.providers.base import LLMAdapter, ModelTrace
from app.utils.retry import TransientError, transient_retry


class AzureOpenAIAdapter(LLMAdapter):
    """Adapter for the Azure AI Foundry unified endpoint (services.ai.azure.com).

    Uses the OpenAI-compatible v1 surface (``{endpoint}/chat/completions``)
    rather than the classic ``*.openai.azure.com`` deployment routes, so a
    plain ``AsyncOpenAI`` client pointed at the Foundry base URL is used.

    Reasoning models on this endpoint (gpt-5.x, Kimi, DeepSeek) require
    ``max_completion_tokens`` and reject non-default ``temperature``; classic
    chat models (e.g. Mistral) use ``max_tokens`` and accept ``temperature``.
    """

    def __init__(self, deployment: str | None = None):
        self.model = deployment or settings.azure_openai_deployment
        # settings.azure_openai_endpoint is the Foundry v1 base, e.g.
        # https://<resource>.services.ai.azure.com/openai/v1
        self._client = AsyncOpenAI(
            api_key=settings.azure_openai_api_key,
            base_url=settings.azure_openai_endpoint.rstrip("/"),
        )

    @property
    def _is_reasoning_model(self) -> bool:
        # Mistral is the only classic (non-reasoning) chat model in use; every
        # other configured deployment is a reasoning model.
        return "mistral" not in self.model.lower()

    @transient_retry(max_attempts=3)
    async def generate(
        self,
        system: str,
        user: str,
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> tuple[str, ModelTrace]:
        start = time.monotonic()

        kwargs: dict = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        if self._is_reasoning_model:
            # Reasoning models: token budget via max_completion_tokens and
            # temperature must stay at the default (1) — omit it entirely.
            kwargs["max_completion_tokens"] = max_tokens
        else:
            kwargs["max_tokens"] = max_tokens
            kwargs["temperature"] = temperature

        try:
            resp = await self._client.chat.completions.create(**kwargs)
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
