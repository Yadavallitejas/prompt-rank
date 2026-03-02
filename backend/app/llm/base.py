"""
PromptRank — LLM Provider Abstraction Layer

Defines the abstract interface and response model that all LLM providers
must implement. This ensures we can swap between OpenAI, Anthropic,
OpenRouter, etc. without changing evaluation logic.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class LLMResponse:
    """Standardised response from any LLM provider."""
    content: str
    tokens_used: int
    latency_ms: int


class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.

    Every concrete provider must implement the `run` method which sends
    the system prompt + user input to the model and returns a standardised
    LLMResponse.
    """

    @abstractmethod
    async def run(
        self,
        system_prompt: str,
        user_input: str,
        *,
        model: str | None = None,
        temperature: float = 0.7,
        seed: int = 42,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        """
        Execute a single LLM call.

        Args:
            system_prompt: The contestant's system prompt being evaluated.
            user_input:    The hidden testcase input text.
            model:         Model identifier (provider-specific). Falls back to default.
            temperature:   Sampling temperature (fixed during contest).
            seed:          Deterministic seed for reproducibility.
            max_tokens:    Maximum output tokens.

        Returns:
            LLMResponse containing the raw text output, token count, and latency.
        """
        ...
