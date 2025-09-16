from __future__ import annotations

from typing import Callable

from ..config import settings
from .base import BaseLLM
from .mock import MockLLM
from .registry import clear_registry, register_model


PROVIDERS: dict[str, Callable[[dict[str, str]], BaseLLM]] = {
    "mock": lambda config: MockLLM(
        model_id=config["model_id"],
        display_name=config.get("display_name", config["model_id"]),
    ),
}


def initialize_models() -> None:
    clear_registry()

    available_ids: set[str] = set()

    for model_config in settings.llm_models:
        if "model_id" not in model_config:
            raise ValueError("llm_models entry requires a 'model_id'.")
        provider = model_config.get("provider", "mock")
        factory = PROVIDERS.get(provider)
        if factory is None:
            raise ValueError(f"Provider '{provider}' not supported yet.")
        model = factory(model_config)
        register_model(model)
        available_ids.add(model.model_id)

    if settings.llm_default_model not in available_ids:
        raise ValueError(
            f"Default model '{settings.llm_default_model}' is not registered."
        )
