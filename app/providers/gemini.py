from __future__ import annotations

import time

from app.config import settings
from app.providers.base import LLMAdapter, ModelTrace
from app.utils.retry import TransientError, transient_retry


class GeminiAdapter(LLMAdapter):
    def __init__(self, model: str = "gemini-2.0-flash"):
        self.model = model
        self._client = None
        self._genai = None

    def _ensure_client(self):
        """Lazy-init: import SDK and configure once, then cache the client."""
        if self._client is None:
            import google.generativeai as genai  # lazy import — avoids cffi issues at module load
            genai.configure(api_key=settings.google_api_key)
            self._genai = genai
            self._client = genai.GenerativeModel(model_name=self.model)

    @transient_retry(max_attempts=3)
    async def generate(
        self,
        system: str,
        user: str,
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> tuple[str, ModelTrace]:
        self._ensure_client()

        start = time.monotonic()
        prompt = f"{system}\n\n{user}"
        config = self._genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
        try:
            resp = await self._client.generate_content_async(prompt, generation_config=config)
        except Exception as exc:
            # Prefer structured status code; fall back to string matching for SDKs
            # that surface errors as plain exceptions without a status_code attribute.
            code = getattr(exc, "status_code", None) or getattr(exc, "code", None)
            if isinstance(code, int) and (code == 429 or code >= 500):
                raise TransientError(str(exc)) from exc
            err = str(exc).lower()
            if "quota" in err or "rate limit" in err or "resource exhausted" in err:
                raise TransientError(str(exc)) from exc
            raise

        latency_ms = (time.monotonic() - start) * 1000
        text = resp.text if resp.text else ""
        usage = getattr(resp, "usage_metadata", None)
        trace = ModelTrace(
            role="gemini",
            model=self.model,
            prompt_tokens=getattr(usage, "prompt_token_count", 0) if usage else 0,
            completion_tokens=getattr(usage, "candidates_token_count", 0) if usage else 0,
            latency_ms=latency_ms,
        )
        return text, trace
