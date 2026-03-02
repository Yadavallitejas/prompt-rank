"""
PromptRank — OpenAI / OpenRouter LLM Provider

Concrete implementation of LLMProvider using the OpenAI Python SDK.
Works with OpenAI, Azure OpenAI, and any OpenAI-compatible endpoint
(e.g. OpenRouter) by configuring `OPENAI_BASE_URL`.
"""

import time
from openai import AsyncOpenAI

from app.config import get_settings
from app.llm.base import LLMProvider, LLMResponse

settings = get_settings()


class OpenAIProvider(LLMProvider):
    """OpenAI-compatible provider (also works with OpenRouter)."""

    def __init__(self) -> None:
        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )
        self.default_model = settings.llm_default_model

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
        target_model = model or self.default_model

        start_ms = time.perf_counter_ns() // 1_000_000

        try:
            response = await self.client.chat.completions.create(
                model=target_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input},
                ],
                temperature=temperature,
                seed=seed,
                max_tokens=max_tokens,
            )

            end_ms = time.perf_counter_ns() // 1_000_000
            latency = end_ms - start_ms

            content = response.choices[0].message.content or ""
            tokens_used = response.usage.total_tokens if response.usage else 0

            return LLMResponse(
                content=content,
                tokens_used=tokens_used,
                latency_ms=latency,
            )

        except Exception as exc:
            end_ms = time.perf_counter_ns() // 1_000_000
            latency = end_ms - start_ms
            # Return error content so scoring can mark it as failed
            return LLMResponse(
                content=f"__LLM_ERROR__: {str(exc)}",
                tokens_used=0,
                latency_ms=latency,
            )
