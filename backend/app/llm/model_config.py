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
    # OpenAI GPT-5 Familie
    ModelConfig(
        model_id="gpt-5.2",
        display_name="OpenAI GPT-5.2",
        provider="openai",
        parameters={
            "temperature": 0.2,
            "max_completion_tokens": 2500,
        },
    ),
    # gpt-5.2-pro entfernt - existiert nicht als Chat-Modell
    ModelConfig(
        model_id="gpt-5.1",
        display_name="OpenAI GPT-5.1",
        provider="openai",
        parameters={
            "max_completion_tokens": 2500,
        },
    ),
    ModelConfig(
        model_id="gpt-5",
        display_name="OpenAI GPT-5",
        provider="openai",
        parameters={
            "max_completion_tokens": 2500,
        },
    ),
    ModelConfig(
        model_id="gpt-5-mini",
        display_name="OpenAI GPT-5 mini",
        provider="openai",
        parameters={
            "max_completion_tokens": 2500,
        },
    ),
    ModelConfig(
        model_id="gpt-5-nano",
        display_name="OpenAI GPT-5 nano",
        provider="openai",
        parameters={
            "max_completion_tokens": 2500,
        },
    ),
    # OpenAI Reasoning Models
    ModelConfig(
        model_id="o3",
        display_name="OpenAI o3",
        provider="openai",
        parameters={
            "max_completion_tokens": 2500,
        },
    ),
    ModelConfig(
        model_id="o4-mini",
        display_name="OpenAI o4-mini",
        provider="openai",
        parameters={
            "max_completion_tokens": 2500,
        },
    ),
    # =================================================================
    # Local Models (Ollama) - Installierte Modelle
    # =================================================================
    # LLaMA Familie
    ModelConfig(
        model_id="llama3.1:8b",
        display_name="LLaMA 3.1 8B (Ollama)",
        provider="ollama",
        parameters={"temperature": 0.1, "max_completion_tokens": 1200},
    ),
    ModelConfig(
        model_id="llama3:latest",
        display_name="LLaMA 3 8B (Ollama)",
        provider="ollama",
        parameters={"temperature": 0.1, "max_completion_tokens": 1200},
    ),
    # Qwen Familie (Alibaba)
    ModelConfig(
        model_id="qwen3:8b",
        display_name="Qwen 3 8B (Ollama)",
        provider="ollama",
        parameters={"temperature": 0.1, "max_completion_tokens": 1200},
    ),
    ModelConfig(
        model_id="qwen3:4b",
        display_name="Qwen 3 4B (Ollama)",
        provider="ollama",
        parameters={"temperature": 0.1, "max_completion_tokens": 1000},
    ),
    # Gemma Familie (Google)
    ModelConfig(
        model_id="gemma2:9b",
        display_name="Gemma 2 9B (Ollama)",
        provider="ollama",
        parameters={"temperature": 0.1, "max_completion_tokens": 1200},
    ),
    # Phi Familie (Microsoft)
    ModelConfig(
        model_id="phi3:mini",
        display_name="Phi-3 Mini (Ollama)",
        provider="ollama",
        parameters={"temperature": 0.1, "max_completion_tokens": 1000},
    ),
    # Mistral
    ModelConfig(
        model_id="mistral:7b",
        display_name="Mistral 7B (Ollama)",
        provider="ollama",
        parameters={"temperature": 0.1, "max_completion_tokens": 1200},
    ),
)


MODEL_CONFIG_BY_ID: dict[str, ModelConfig] = {config.model_id: config for config in MODEL_CONFIGS}


__all__ = ["ModelConfig", "MODEL_CONFIGS", "MODEL_CONFIG_BY_ID"]
