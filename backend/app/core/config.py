from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="PROJECT_HELPER_",
        extra="ignore",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    app_name: str = "project-helper"
    database_url: str = "sqlite+aiosqlite:///./project-helper.db"
    workspace_root: Path = Path("./workspace")
    deepseek_api_key: str | None = None
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"
    analysis_delay_ms: int = 150
    testing_repo_map: dict[str, str] = Field(default_factory=dict)

    @classmethod
    def from_overrides(cls, overrides: dict[str, Any] | None = None) -> "Settings":
        return cls(**(overrides or {}))
