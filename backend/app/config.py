from typing import Sequence

from pydantic import Field
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

    class Config:
        env_prefix = "LLM_PIPELINE_"
        case_sensitive = False


settings = Settings()
