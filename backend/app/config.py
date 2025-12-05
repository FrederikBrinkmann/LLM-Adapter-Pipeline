from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


def default_llm_model_ids() -> list[str]:
    return ["llama3"]


def default_database_path() -> Path:
    root = Path(__file__).resolve().parent.parent.parent
    data_dir = root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "pipeline.db"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="LLM_PIPELINE_",
        case_sensitive=False,
        env_file=(".env",),
        extra="ignore",  # allow unrelated env vars (z. B. MAIL_* für mail_ingest.py)
    )

    api_title: str = Field(default="LLM Adapter Pipeline API")
    api_description: str = Field(
        default="HTTP API to manage ingestion and processing jobs for the LLM adapter pipeline."
    )
    api_version: str = Field(default="0.1.0")

    backend_cors_origins: Sequence[str] = Field(
        default=(
            "http://localhost",
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
        ),
        description="Origins allowed to access the API via CORS.",
    )

    llm_default_model: str = Field(default="llama3")
    llm_model_ids: list[str] = Field(default_factory=default_llm_model_ids)
    llm_model_overrides: dict[str, dict[str, Any]] = Field(default_factory=dict)

    database_path: Path = Field(default_factory=default_database_path)
    database_url_override: str | None = Field(default=None, alias="database_url")
    database_echo: bool = Field(default=False)

    openai_api_key: str | None = Field(default=None)
    openai_api_base: str = Field(default="https://api.openai.com/v1")
    openai_timeout_seconds: float = Field(default=30.0)

    ollama_base_url: str = Field(default="http://127.0.0.1:11434")
    ollama_timeout_seconds: float = Field(default=60.0)

    target_api_base_url: str | None = Field(default=None)
    target_api_token: str | None = Field(default=None)
    target_api_tickets_path: str = Field(default="/tickets")
    target_timeout_seconds: float = Field(default=10.0)

    worker_poll_interval: float = Field(default=1.0)
    auto_submit_enabled: bool = Field(default=False, description="Submit completed jobs automatically")
    auto_submit_api_base: str = Field(
        default="http://127.0.0.1:8000",
        description="Base URL of the pipeline API for auto-submit",
    )
    auto_submit_allow_missing_fields: bool = Field(
        default=False, description="Submit even if missing_fields are present"
    )

    @computed_field
    @property
    def database_url(self) -> str:
        if self.database_url_override:
            return self.database_url_override
        return f"sqlite:///{self.database_path}"


settings = Settings()
