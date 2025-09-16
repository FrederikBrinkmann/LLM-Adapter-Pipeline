from __future__ import annotations

from pathlib import Path
from typing import Sequence

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings


def default_llm_models() -> list[dict[str, str]]:
    return [
        {
            "model_id": "mock-basic",
            "display_name": "Mock Model (lokal)",
            "provider": "mock",
        },
        {
            "model_id": "mock-advanced",
            "display_name": "Mock Advanced (lokal)",
            "provider": "mock",
        },
    ]


def default_database_path() -> Path:
    root = Path(__file__).resolve().parent.parent.parent
    data_dir = root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "pipeline.db"


class Settings(BaseSettings):
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

    llm_default_model: str = Field(default="mock-basic")
    llm_models: list[dict[str, str]] = Field(default_factory=default_llm_models)

    database_path: Path = Field(default_factory=default_database_path)
    database_url_override: str | None = Field(default=None, alias="database_url")
    database_echo: bool = Field(default=False)

    target_api_base_url: str | None = Field(default=None)
    target_api_token: str | None = Field(default=None)
    target_api_tickets_path: str = Field(default="/tickets")
    target_timeout_seconds: float = Field(default=10.0)

    worker_poll_interval: float = Field(default=1.0)

    class Config:
        env_prefix = "LLM_PIPELINE_"
        case_sensitive = False

    @computed_field
    @property
    def database_url(self) -> str:
        if self.database_url_override:
            return self.database_url_override
        return f"sqlite:///{self.database_path}"


settings = Settings()
