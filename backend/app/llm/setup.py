from __future__ import annotations

from typing import Callable

from ..config import settings
from .base import BaseLLM, LLMError
from .model_registry import MODEL_REGISTRY, ModelDefinition
from .ollama_adapter import OllamaAdapter
from .openai_adapter import OpenAIAdapter
from .registry import clear_registry, register_model


PROVIDERS: dict[str, Callable[[ModelDefinition], BaseLLM]] = {
    "openai": lambda definition: OpenAIAdapter(
        model_id=definition.model_id,
        display_name=definition.display_name,
        parameters=definition.parameters,
    ),
    "ollama": lambda definition: OllamaAdapter(
        model_id=definition.model_id,
        display_name=definition.display_name,
        parameters=definition.parameters,
    ),
}


def initialize_models() -> None:
    clear_registry()

    available_ids: set[str] = set()

    for model_id in settings.llm_model_ids:
        try:
            base_definition = MODEL_REGISTRY[model_id]
        except KeyError as exc:
            raise ValueError(
                f"Model id '{model_id}' not found in registry."
            ) from exc

        overrides = settings.llm_model_overrides.get(model_id)
        definition = base_definition.apply_overrides(overrides)

        factory = PROVIDERS.get(definition.provider)
        if factory is None:
            raise ValueError(f"Provider '{definition.provider}' not supported yet.")

        try:
            model = factory(definition)
        except LLMError as exc:
            raise ValueError(
                f"Failed to initialise model '{definition.model_id}': {exc}"
            ) from exc
        register_model(model)
        available_ids.add(model.model_id)

    if settings.llm_default_model not in available_ids:
        raise ValueError(
            f"Default model '{settings.llm_default_model}' is not registered."
        )
