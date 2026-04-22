"""Application settings via Pydantic Settings.

All values are read from environment variables (or .env file).
No secrets are hardcoded here.
"""

from __future__ import annotations

import functools
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralised config — loaded once per process via get_settings()."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ------------------------------------------------------------------
    # LLM
    # ------------------------------------------------------------------
    gemini_api_key: str = ""  # Empty by default; tests can run without a real key
    litellm_model: str = "gemini/gemini-2.5-flash"
    llm_temperature: float = 0.3
    # Gemini 2.5 flash 支援最大 output 約 65K tokens；
    # thinking 模式會吃掉部分 budget。16384 搭配 prompt 字數控制
    # 提供充裕的硬性安全網，即使 LLM 話多也不會被截斷。
    llm_max_tokens: int = 16384
    llm_timeout_seconds: float = 30.0

    # ------------------------------------------------------------------
    # App
    # ------------------------------------------------------------------
    app_env: Literal["dev", "staging", "prod"] = "dev"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"


@functools.lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings instance.

    Use this as a FastAPI dependency::

        @router.get("/")
        def handler(settings: Settings = Depends(get_settings)):
            ...
    """
    return Settings()
