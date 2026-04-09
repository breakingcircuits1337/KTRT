from __future__ import annotations

import time

from app.config import settings
from app.providers.base import LLMAdapter, ModelTrace
from app.utils.retry import TransientError, transient_retry


class GeminiAdapter(LLMAdapter):
    def __init__(self, model: str = "gemini-2.0-flash"):
        self.model = model

    def _get_client(self):
        import google.generativeai as genai  # lazy import
        genai.configure(api_key=settings.google_api_key)
        return genai.GenerativeModel(model_name=self.model), genai

    @transient_retry(max_attempts=3)
    async def generate(
        self,
        system: str,
        user: str,
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> tuple[str, ModelTrace]:
        import google.generativeai as genai  # lazy import
        client, genai = self._get_client()

        start = time.monotonic()
        prompt = f"{system}\n\n{user}"
        config = genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
        try:
            resp = await client.generate_content_async(prompt, generation_config=config)
        except Exception as exc:
            err = str(exc).lower()
            if "quota" in err or "rate" in err or "503" in err or "500" in err:
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
