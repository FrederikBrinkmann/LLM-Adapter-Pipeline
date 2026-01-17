from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from .model_config import ModelConfig


PROVIDER_DEFAULTS: dict[str, dict[str, Any]] = {
    "openai": {
        "temperature": 0.0,
        "max_tokens": 900,
    },
    "ollama": {
        "temperature": 0.2,
        "top_p": 0.9,
        "max_tokens": 700,
    },
}


@dataclass(frozen=True)
class ModelSpec:
    model_id: str
    display_name: str
    provider: str
    parameters: dict[str, Any] = field(default_factory=dict)


def resolve_model_spec(config: ModelConfig, overrides: Mapping[str, Any] | None) -> ModelSpec:
    display_name = config.display_name
    provider = config.provider

    if overrides:
        display_name = overrides.get("display_name", display_name)
        provider = overrides.get("provider", provider)

    parameters: dict[str, Any] = dict(PROVIDER_DEFAULTS.get(provider, {}))
    parameters.update(config.parameters)

    if overrides:
        override_params = overrides.get("parameters")
        if isinstance(override_params, Mapping):
            parameters.update(override_params)

    return ModelSpec(
        model_id=config.model_id,
        display_name=display_name,
        provider=provider,
        parameters=parameters,
    )


__all__ = ["PROVIDER_DEFAULTS", "ModelSpec", "resolve_model_spec"]
