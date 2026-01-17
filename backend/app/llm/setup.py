from __future__ import annotations

from ..config import settings
from .adapter import LLMAdapter, supports_provider
from .base import LLMError
from .model_config import MODEL_CONFIG_BY_ID
from .model_spec import resolve_model_spec
from .registry import clear_registry, register_model


def initialize_models() -> None:
    clear_registry()

    available_ids: set[str] = set()

    for model_id in settings.llm_model_ids:
        try:
            base_config = MODEL_CONFIG_BY_ID[model_id]
        except KeyError as exc:
            raise ValueError(f"Model id '{model_id}' not found in config.") from exc

        overrides = settings.llm_model_overrides.get(model_id)
        definition = resolve_model_spec(base_config, overrides)

        if not supports_provider(definition.provider):
            raise ValueError(f"Provider '{definition.provider}' not supported yet.")
        try:
            model = LLMAdapter(
                model_id=definition.model_id,
                display_name=definition.display_name,
                provider=definition.provider,
                parameters=definition.parameters,
            )
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
