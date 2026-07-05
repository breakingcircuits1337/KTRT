from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.providers.base import LLMAdapter

# Default role → (module_path, class_name, model_name)
# Azure AI Foundry is the primary provider. Deployment names must match what you
# configured in your Azure AI Foundry project. Other providers remain available
# as per-request overrides via the model aliases below.
_DEFAULTS: dict[str, tuple[str, str, str | None]] = {
    # Deployment names below match the live Azure AI Foundry resource
    # (brokencircuits-1334) validated against /openai/v1/chat/completions.
    # Fast factual retrieval
    "researcher": ("app.providers.azure_openai", "AzureOpenAIAdapter", "DeepSeek-V4-Pro"),
    # Evidence weighing — Kimi's extended reasoning excels here
    "evidence": ("app.providers.azure_openai", "AzureOpenAIAdapter", "Kimi-K2.6"),
    # Strategic planning — GPT-5.5 flagship reasoning
    "planner": ("app.providers.azure_openai", "AzureOpenAIAdapter", "gpt-5.5"),
    # Adversarial critique — Mistral Large 3 (classic chat model)
    "critic": ("app.providers.azure_openai", "AzureOpenAIAdapter", "Mistral-Large-3"),
    # Final verdict — GPT-5.5 for authoritative evaluation
    "judge": ("app.providers.azure_openai", "AzureOpenAIAdapter", "gpt-5.5"),
    # Code generation — GPT-5.5 (gpt-5.3-codex is Responses-API only, unusable here)
    "builder": ("app.providers.azure_openai", "AzureOpenAIAdapter", "gpt-5.5"),
    # Debugging — GPT-5.5
    "debugger": ("app.providers.azure_openai", "AzureOpenAIAdapter", "gpt-5.5"),
}

_MODEL_ALIASES: dict[str, tuple[str, str, str | None]] = {
    # ── Azure AI Foundry — your deployed models ──────────────────
    "azure:gpt-5.4-pro": ("app.providers.azure_openai", "AzureOpenAIAdapter", "gpt-5.4-pro"),
    "azure:gpt-5.4": ("app.providers.azure_openai", "AzureOpenAIAdapter", "gpt-5.4"),
    "azure:gpt-5.1-codex-max": ("app.providers.azure_openai", "AzureOpenAIAdapter", "gpt-5.1-codex-max"),
    "azure:deepseek-v3.2": ("app.providers.azure_openai", "AzureOpenAIAdapter", "deepseek-v3.2"),
    "azure:deepseek-v3.2-speciale": ("app.providers.azure_openai", "AzureOpenAIAdapter", "deepseek-v3.2-speciale"),
    "azure:mistral-large-3": ("app.providers.azure_openai", "AzureOpenAIAdapter", "mistral-large-3"),
    "azure:kimi-k2-thinking": ("app.providers.azure_openai", "AzureOpenAIAdapter", "kimi-k2-thinking"),
    # ── Anthropic (fallback / override) ──────────────────────────
    "claude-sonnet-4-6": ("app.providers.anthropic", "AnthropicAdapter", "claude-sonnet-4-6"),
    "claude-opus-4-6": ("app.providers.anthropic", "AnthropicAdapter", "claude-opus-4-6"),
    "claude-haiku-4-5": ("app.providers.anthropic", "AnthropicAdapter", "claude-haiku-4-5-20251001"),
    # ── Gemini (fallback / override) ─────────────────────────────
    "gemini-2.0-flash": ("app.providers.gemini", "GeminiAdapter", "gemini-2.0-flash"),
    "gemini-1.5-pro": ("app.providers.gemini", "GeminiAdapter", "gemini-1.5-pro"),
    # ── Groq (fallback / override) ───────────────────────────────
    "groq:llama-3.3-70b": ("app.providers.groq", "GroqAdapter", "llama-3.3-70b-versatile"),
    # ── Mistral direct API (fallback / override) ─────────────────
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
