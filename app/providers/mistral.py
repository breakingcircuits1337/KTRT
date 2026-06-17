from __future__ import annotations

import time

from mistralai import Mistral
from mistralai.models import SDKError

from app.config import settings
from app.providers.base import LLMAdapter, ModelTrace
from app.utils.retry import TransientError, transient_retry


class MistralAdapter(LLMAdapter):
    def __init__(self, model: str = "mistral-large-latest"):
        self.model = model
        self._client = Mistral(api_key=settings.mistral_api_key)

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
            resp = await self._client.chat.complete_async(
                model=self.model,
                temperature=temperature,
                max_tokens=max_tokens,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
        except SDKError as exc:
            if exc.status_code == 429 or exc.status_code >= 500:
                raise TransientError(str(exc)) from exc
            raise
        except Exception as exc:
            raise

        latency_ms = (time.monotonic() - start) * 1000
        text = resp.choices[0].message.content or "" if resp.choices else ""
        usage = resp.usage
        trace = ModelTrace(
            role="mistral",
            model=self.model,
            prompt_tokens=usage.prompt_tokens if usage else 0,
            completion_tokens=usage.completion_tokens if usage else 0,
            latency_ms=latency_ms,
        )
        return text, trace
