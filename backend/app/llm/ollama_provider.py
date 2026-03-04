"""
PromptRank — Ollama LLM Provider (Local Testing Only)

Connects to a locally running Ollama instance at OLLAMA_BASE_URL
(default http://localhost:11434). Uses the /api/chat endpoint with
the same system-prompt + user-input structure as the OpenAI provider.

NOT intended for production contests — use OpenAI for that.
"""

import time
import httpx
import logging

from app.config import get_settings
from app.llm.base import LLMProvider, LLMResponse

settings = get_settings()
logger = logging.getLogger(__name__)


class OllamaProvider(LLMProvider):
    """Local Ollama provider for cost-free development and testing."""

    def __init__(self) -> None:
        self.base_url = settings.ollama_base_url.rstrip("/")
        self.default_model = settings.ollama_default_model
        self._verify_model_available()

    def _verify_model_available(self) -> None:
        """Check that the configured model is pulled in Ollama. Logs a clear warning if not."""
        try:
            resp = httpx.get(f"{self.base_url}/api/tags", timeout=5.0)
            resp.raise_for_status()
            available = [m["name"] for m in resp.json().get("models", [])]
            # Normalise: ollama list shows "llama3.1:8b", payload uses same
            if not any(
                self.default_model == name or self.default_model.split(":")[0] == name.split(":")[0]
                for name in available
            ):
                logger.warning(
                    "[OllamaProvider] Model '%s' is NOT available in Ollama. "
                    "Pull it first: `ollama pull %s`. "
                    "Available models: %s",
                    self.default_model,
                    self.default_model,
                    available,
                )
            else:
                logger.info("[OllamaProvider] Model '%s' is available ✓", self.default_model)
        except Exception as exc:
            logger.warning(
                "[OllamaProvider] Could not connect to Ollama at %s: %s. "
                "Make sure Ollama is running on the host.",
                self.base_url,
                exc,
            )

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
        # Overwrite remote model requests (e.g. gpt-4o-mini) with the local ollama model
        if model and ("gpt" in model.lower() or "claude" in model.lower() or "o1" in model.lower()):
            target_model = self.default_model
        else:
            target_model = model or self.default_model

        payload = {
            "model": target_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input},
            ],
            "stream": False,
            "options": {
                "temperature": temperature,
                "seed": seed,
                "num_predict": max_tokens,
            },
        }

        start_ms = time.perf_counter_ns() // 1_000_000

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()

            end_ms = time.perf_counter_ns() // 1_000_000
            latency = end_ms - start_ms

            content = data.get("message", {}).get("content", "")
            # Ollama reports token counts in eval_count / prompt_eval_count
            tokens_used = data.get("eval_count", 0) + data.get("prompt_eval_count", 0)

            return LLMResponse(
                content=content,
                tokens_used=tokens_used,
                latency_ms=latency,
            )

        except Exception as exc:
            end_ms = time.perf_counter_ns() // 1_000_000
            latency = end_ms - start_ms
            return LLMResponse(
                content=f"__LLM_ERROR__: {str(exc)}",
                tokens_used=0,
                latency_ms=latency,
            )
