"""
PromptRank — Application Configuration
Loads settings from environment variables via pydantic-settings.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # ── Database ──────────────────────────────────────────────
    database_url: str = "postgresql+asyncpg://promptrank:promptrank@localhost:5432/promptrank"

    # ── Redis ─────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"

    # ── JWT Auth ──────────────────────────────────────────────
    secret_key: str = "change-me-to-a-random-secret-key"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # ── LLM Provider ─────────────────────────────────────────
    llm_provider: str = "openai"
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    llm_default_model: str = "gpt-4o-mini"

    # ── Ollama (local testing only) ──────────────────────────
    ollama_base_url: str = "http://localhost:11434"
    ollama_default_model: str = "llama3"

    # ── Evaluation Defaults ──────────────────────────────────
    eval_sampling_n: int = 5
    eval_fixed_temperature: float = 0.7
    eval_max_tokens: int = 2048

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


@lru_cache()
def get_settings() -> Settings:
    return Settings()
