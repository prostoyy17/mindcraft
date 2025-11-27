from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-level configuration loaded from environment variables."""

    openai_api_key: str
    openai_model: str = "gpt-4.1-mini"
    app_name: str = "MindCraft API"
    allow_origins: list[str] = ["*"]
    ai_mode: Literal["mock", "live"] = "mock"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def use_live_ai(self) -> bool:
        return self.ai_mode == "live"


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[arg-type]
