from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ModelConfig:
    model_id: str
    display_name: str
    provider: str
    parameters: dict[str, Any] = field(default_factory=dict)


MODEL_CONFIGS: tuple[ModelConfig, ...] = (
    ModelConfig(
        model_id="llama3",
        display_name="LLaMA 3 (Ollama)",
        provider="ollama",
        parameters={
            "temperature": 0.1,
            "max_tokens": 800,
        },
    ),
    ModelConfig(
        model_id="gpt-4o-mini",
        display_name="OpenAI GPT-4o mini",
        provider="openai",
    ),
    ModelConfig(
        model_id="gpt-4o",
        display_name="OpenAI GPT-4o",
        provider="openai",
        parameters={
            "max_tokens": 1200,
        },
    ),
    ModelConfig(
        model_id="gpt-4.1",
        display_name="OpenAI GPT-4.1",
        provider="openai",
        parameters={
            "max_tokens": 1200,
        },
    ),
    ModelConfig(
        model_id="gpt-4.1-mini",
        display_name="OpenAI GPT-4.1 mini",
        provider="openai",
    ),

    ModelConfig(
    model_id="gpt-5.2",
    display_name="OpenAI GPT-5.2",
    provider="openai",
    parameters={
        "temperature": 0.2,
        "max_tokens": 1200,
    },
  ),
    ModelConfig(
        model_id="mistral",
        display_name="Mistral 7B (Ollama)",
        provider="ollama",
    ),
    ModelConfig(
        model_id="phi3",
        display_name="Phi-3 (Ollama)",
        provider="ollama",
        parameters={
            "temperature": 0.1,
        },
    ),
)


MODEL_CONFIG_BY_ID: dict[str, ModelConfig] = {config.model_id: config for config in MODEL_CONFIGS}


__all__ = ["ModelConfig", "MODEL_CONFIGS", "MODEL_CONFIG_BY_ID"]
