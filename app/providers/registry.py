from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.providers.base import LLMAdapter

# Default role → (module_path, class_name, model_name)
_DEFAULTS: dict[str, tuple[str, str, str | None]] = {
    "researcher": ("app.providers.mistral", "MistralAdapter", "mistral-large-latest"),
    "evidence": ("app.providers.anthropic", "AnthropicAdapter", "claude-sonnet-4-6"),
    "planner": ("app.providers.anthropic", "AnthropicAdapter", "claude-sonnet-4-6"),
    "critic": ("app.providers.groq", "GroqAdapter", "llama-3.3-70b-versatile"),
    "judge": ("app.providers.gemini", "GeminiAdapter", "gemini-2.0-flash"),
    "builder": ("app.providers.anthropic", "AnthropicAdapter", "claude-sonnet-4-6"),
    "debugger": ("app.providers.azure_openai", "AzureOpenAIAdapter", None),
}

_MODEL_ALIASES: dict[str, tuple[str, str, str | None]] = {
    # Anthropic
    "claude-sonnet-4-6": ("app.providers.anthropic", "AnthropicAdapter", "claude-sonnet-4-6"),
    "claude-opus-4-6": ("app.providers.anthropic", "AnthropicAdapter", "claude-opus-4-6"),
    "claude-haiku-4-5": ("app.providers.anthropic", "AnthropicAdapter", "claude-haiku-4-5-20251001"),
    # Azure
    "azure:gpt-4.1": ("app.providers.azure_openai", "AzureOpenAIAdapter", "gpt-4.1"),
    "azure:gpt-4o": ("app.providers.azure_openai", "AzureOpenAIAdapter", "gpt-4o"),
    # Gemini
    "gemini-2.0-flash": ("app.providers.gemini", "GeminiAdapter", "gemini-2.0-flash"),
    "gemini-1.5-pro": ("app.providers.gemini", "GeminiAdapter", "gemini-1.5-pro"),
    # Groq
    "groq:llama-3.3-70b": ("app.providers.groq", "GroqAdapter", "llama-3.3-70b-versatile"),
    # Mistral
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
