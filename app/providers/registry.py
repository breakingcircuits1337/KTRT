from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.providers.base import LLMAdapter

# Default role → (module_path, class_name, model_name)
# Azure AI Foundry is the primary provider. Other providers remain available via
# per-request overrides using the model aliases below.
_DEFAULTS: dict[str, tuple[str, str, str | None]] = {
    # Fast research/retrieval — GPT-4o balances speed and quality
    "researcher": ("app.providers.azure_openai", "AzureOpenAIAdapter", "gpt-4o"),
    # Deep synthesis — GPT-4.1 flagship for highest-quality outputs
    "evidence": ("app.providers.azure_openai", "AzureOpenAIAdapter", "gpt-4.1"),
    "planner": ("app.providers.azure_openai", "AzureOpenAIAdapter", "gpt-4.1"),
    # Critique pass — GPT-4o is fast enough and sharp enough for adversarial review
    "critic": ("app.providers.azure_openai", "AzureOpenAIAdapter", "gpt-4o"),
    # Final verdict — GPT-4.1 for authoritative evaluation
    "judge": ("app.providers.azure_openai", "AzureOpenAIAdapter", "gpt-4.1"),
    # Code generation — GPT-4.1 for best correctness
    "builder": ("app.providers.azure_openai", "AzureOpenAIAdapter", "gpt-4.1"),
    # Debugging — GPT-4.1 with strong code reasoning
    "debugger": ("app.providers.azure_openai", "AzureOpenAIAdapter", "gpt-4.1"),
}

_MODEL_ALIASES: dict[str, tuple[str, str, str | None]] = {
    # ── Azure (primary) ──────────────────────────────────────────
    "azure:gpt-4.1": ("app.providers.azure_openai", "AzureOpenAIAdapter", "gpt-4.1"),
    "azure:gpt-4.1-mini": ("app.providers.azure_openai", "AzureOpenAIAdapter", "gpt-4.1-mini"),
    "azure:gpt-4o": ("app.providers.azure_openai", "AzureOpenAIAdapter", "gpt-4o"),
    "azure:gpt-4o-mini": ("app.providers.azure_openai", "AzureOpenAIAdapter", "gpt-4o-mini"),
    # ── Anthropic (fallback / override) ──────────────────────────
    "claude-sonnet-4-6": ("app.providers.anthropic", "AnthropicAdapter", "claude-sonnet-4-6"),
    "claude-opus-4-6": ("app.providers.anthropic", "AnthropicAdapter", "claude-opus-4-6"),
    "claude-haiku-4-5": ("app.providers.anthropic", "AnthropicAdapter", "claude-haiku-4-5-20251001"),
    # ── Gemini (fallback / override) ─────────────────────────────
    "gemini-2.0-flash": ("app.providers.gemini", "GeminiAdapter", "gemini-2.0-flash"),
    "gemini-1.5-pro": ("app.providers.gemini", "GeminiAdapter", "gemini-1.5-pro"),
    # ── Groq (fallback / override) ───────────────────────────────
    "groq:llama-3.3-70b": ("app.providers.groq", "GroqAdapter", "llama-3.3-70b-versatile"),
    # ── Mistral (fallback / override) ────────────────────────────
    "mistral-large-latest": ("app.providers.mistral", "MistralAdapter", "mistral-large-latest"),
    "mistral-small-latest": ("app.providers.mistral", "MistralAdapter", "mistral-small-latest"),
}


def _load(module_path: str, class_name: str, model_name: str | None) -> "LLMAdapter":
    import importlib
    module = importlib.import_module(module_path)
    cls = getattr(module, class_name)
    return cls(model_name) if model_name else cls()


def get_adapter(model_id: str) -> "LLMAdapter":
    """Resolve a model identifier string to a concrete adapter instance."""
    entry = _MODEL_ALIASES.get(model_id)
    if entry is None:
        raise ValueError(f"Unknown model id: {model_id!r}. Available: {list(_MODEL_ALIASES)}")
    return _load(*entry)


def get_role_adapter(role: str, override_model: str | None = None) -> "LLMAdapter":
    """Return the adapter for a named role, optionally overriding the model."""
    if override_model:
        return get_adapter(override_model)
    if role not in _DEFAULTS:
        raise ValueError(f"Unknown role: {role!r}. Available: {list(_DEFAULTS)}")
    return _load(*_DEFAULTS[role])
