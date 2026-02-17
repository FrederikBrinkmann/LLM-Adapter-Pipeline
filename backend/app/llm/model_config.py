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
            "max_tokens": 1200,
        },
    ),
    ModelConfig(
        model_id="gpt-5.2-pro",
        display_name="OpenAI GPT-5.2 Pro",
        provider="openai",
        parameters={
            "temperature": 0.2,
            "max_tokens": 1500,
        },
    ),
    ModelConfig(
        model_id="gpt-5.1",
        display_name="OpenAI GPT-5.1",
        provider="openai",
        parameters={
            "max_tokens": 1200,
        },
    ),
    ModelConfig(
        model_id="gpt-5",
        display_name="OpenAI GPT-5",
        provider="openai",
        parameters={
            "max_tokens": 1200,
        },
    ),
    ModelConfig(
        model_id="gpt-5-mini",
        display_name="OpenAI GPT-5 mini",
        provider="openai",
    ),
    ModelConfig(
        model_id="gpt-5-nano",
        display_name="OpenAI GPT-5 nano",
        provider="openai",
    ),
    # OpenAI Reasoning Models
    ModelConfig(
        model_id="o3",
        display_name="OpenAI o3",
        provider="openai",
        parameters={
            "max_tokens": 1500,
        },
    ),
    ModelConfig(
        model_id="o4-mini",
        display_name="OpenAI o4-mini",
        provider="openai",
    ),
    # Local Models (Ollama)
    # LLaMA 3.1 Familie
    ModelConfig(
        model_id="llama3.1-8b",
        display_name="LLaMA 3.1 8B (Ollama)",
        provider="ollama",
        parameters={"temperature": 0.1, "max_tokens": 800},
    ),
    ModelConfig(
        model_id="llama3.1-70b",
        display_name="LLaMA 3.1 70B (Ollama)",
        provider="ollama",
        parameters={"temperature": 0.1, "max_tokens": 1200},
    ),
    ModelConfig(
        model_id="llama3.1-405b",
        display_name="LLaMA 3.1 405B (Ollama)",
        provider="ollama",
        parameters={"temperature": 0.1, "max_tokens": 1200},
    ),
    # Gemma 3 Familie
    ModelConfig(
        model_id="gemma3-2b",
        display_name="Gemma 3 2B (Ollama)",
        provider="ollama",
    ),
    ModelConfig(
        model_id="gemma3-9b",
        display_name="Gemma 3 9B (Ollama)",
        provider="ollama",
    ),
    ModelConfig(
        model_id="gemma3-27b",
        display_name="Gemma 3 27B (Ollama)",
        provider="ollama",
        parameters={"max_tokens": 1200},
    ),
    # Gemma 2 Familie
    ModelConfig(
        model_id="gemma2-2b",
        display_name="Gemma 2 2B (Ollama)",
        provider="ollama",
    ),
    ModelConfig(
        model_id="gemma2-9b",
        display_name="Gemma 2 9B (Ollama)",
        provider="ollama",
    ),
    ModelConfig(
        model_id="gemma2-27b",
        display_name="Gemma 2 27B (Ollama)",
        provider="ollama",
        parameters={"max_tokens": 1200},
    ),
    # Gemma 1 Familie
    ModelConfig(
        model_id="gemma-2b",
        display_name="Gemma 2B (Ollama)",
        provider="ollama",
    ),
    ModelConfig(
        model_id="gemma-7b",
        display_name="Gemma 7B (Ollama)",
        provider="ollama",
    ),
    # Phi-3 Familie
    ModelConfig(
        model_id="phi3-3b",
        display_name="Phi-3 3B (Ollama)",
        provider="ollama",
        parameters={"temperature": 0.1},
    ),
    ModelConfig(
        model_id="phi3-14b",
        display_name="Phi-3 14B (Ollama)",
        provider="ollama",
        parameters={"temperature": 0.1},
    ),
    # OLMo Familie
    ModelConfig(
        model_id="olmo-3",
        display_name="OLMo 3 (Ollama)",
        provider="ollama",
    ),
    ModelConfig(
        model_id="olmo-3.1",
        display_name="OLMo 3.1 (Ollama)",
        provider="ollama",
    ),
    # NVIDIA Nemotron
    ModelConfig(
        model_id="nemotron-3-nano",
        display_name="Nemotron 3 Nano (Ollama)",
        provider="ollama",
    ),
    # DeepSeek
    ModelConfig(
        model_id="deepseek-v3.1",
        display_name="DeepSeek V3.1 (Ollama)",
        provider="ollama",
        parameters={"max_tokens": 1200},
    ),
)


MODEL_CONFIG_BY_ID: dict[str, ModelConfig] = {config.model_id: config for config in MODEL_CONFIGS}


__all__ = ["ModelConfig", "MODEL_CONFIGS", "MODEL_CONFIG_BY_ID"]
