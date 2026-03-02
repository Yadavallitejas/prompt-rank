"""
PromptRank — LLM Provider Factory

Returns the correct LLMProvider instance based on the application config.
"""

from app.config import get_settings
from app.llm.base import LLMProvider
from app.llm.openai_provider import OpenAIProvider
from app.llm.ollama_provider import OllamaProvider


_provider_cache: LLMProvider | None = None


def get_llm_provider() -> LLMProvider:
    """
    Factory — returns a singleton LLMProvider based on settings.llm_provider.

    Supported providers:
        - "openai"  / "openrouter" — production (remote API)
        - "ollama"                 — local testing only

    Raises:
        ValueError if the configured provider is not supported.
    """
    global _provider_cache
    if _provider_cache is not None:
        return _provider_cache

    settings = get_settings()
    provider_name = settings.llm_provider.lower()

    if provider_name in ("openai", "openrouter"):
        _provider_cache = OpenAIProvider()
    elif provider_name == "ollama":
        _provider_cache = OllamaProvider()
    else:
        raise ValueError(
            f"Unsupported LLM provider: '{provider_name}'. "
            f"Supported: openai, openrouter, ollama"
        )

    return _provider_cache
