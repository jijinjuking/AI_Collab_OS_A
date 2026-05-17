"""Application configuration via pydantic-settings."""

from pathlib import Path
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Global application settings, loaded from environment / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Application ---
    app_name: str = "AI-Collab-OS"
    app_env: Literal["development", "production", "testing"] = "development"
    debug: bool = True
    secret_key: str = "change-me-to-a-random-string-at-least-32-chars"
    host: str = "0.0.0.0"
    port: int = 8000

    # --- Database ---
    database_url: str = "sqlite+aiosqlite:///./data/dev.db"
    db_pool_size: int = 20
    db_max_overflow: int = 10
    db_pool_timeout: int = 30
    db_pool_recycle: int = 1800

    # --- Redis ---
    redis_url: str = "redis://localhost:6379/0"
    redis_max_connections: int = 50

    # --- JWT ---
    jwt_secret_key: str = "change-me-jwt-secret-at-least-32-chars"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 1440  # 24 hours

    # --- LLM ---
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    ollama_base_url: str = "http://localhost:11434"
    default_llm_model: str = "gpt-4o"
    default_llm_provider: str = "openai"

    # --- File Storage ---
    workspace_root: str = "./workspaces"

    # --- Docker Sandbox ---
    sandbox_enabled: bool = False
    sandbox_image: str = "python:3.11-slim"
    sandbox_timeout: int = 60
    sandbox_memory_limit: str = "512m"

    # --- CORS ---
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # --- Rate Limiting ---
    rate_limit_enabled: bool = True
    rate_limit_user: int = 200  # requests per window (authenticated)
    rate_limit_ip: int = 60  # requests per window (anonymous)
    rate_limit_window: int = 60  # window size in seconds

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            import json
            return json.loads(v)
        return v

    @property
    def is_dev(self) -> bool:
        return self.app_env == "development"

    @property
    def is_prod(self) -> bool:
        return self.app_env == "production"

    @property
    def workspace_path(self) -> Path:
        return Path(self.workspace_root).resolve()


# Singleton instance
settings = Settings()
