from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class ModelDefinition:
    """Static model metadata used to build runtime adapters."""

    model_id: str
    display_name: str
    provider: str
    parameters: dict[str, Any] = field(default_factory=dict)

    def apply_overrides(self, overrides: Mapping[str, Any] | None) -> "ModelDefinition":
        if not overrides:
            return self

        display_name = overrides.get("display_name", self.display_name)
        provider = overrides.get("provider", self.provider)

        parameters = dict(self.parameters)
        override_params = overrides.get("parameters")
        if isinstance(override_params, Mapping):
            parameters.update(override_params)

        return ModelDefinition(
            model_id=self.model_id,
            display_name=display_name,
            provider=provider,
            parameters=parameters,
        )


MODEL_REGISTRY: dict[str, ModelDefinition] = {
    "llama3": ModelDefinition(
        model_id="llama3",
        display_name="LLaMA 3 (Ollama)",
        provider="ollama",
        parameters={
            "temperature": 0.1,
            "top_p": 0.9,
            "max_tokens": 800,
        },
    ),
    "gpt-4o-mini": ModelDefinition(
        model_id="gpt-4o-mini",
        display_name="OpenAI GPT-4o mini",
        provider="openai",
        parameters={
            "temperature": 0.0,
            "max_completion_tokens": 900,
        },
    ),
    "gpt-4o": ModelDefinition(
        model_id="gpt-4o",
        display_name="OpenAI GPT-4o",
        provider="openai",
        parameters={
            "temperature": 0.0,
            "max_completion_tokens": 1200,
        },
    ),
}


__all__ = ["MODEL_REGISTRY", "ModelDefinition"]
