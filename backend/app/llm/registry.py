from __future__ import annotations

from typing import Dict

from .base import BaseLLM


REGISTERED_MODELS: Dict[str, BaseLLM] = {}


def register_model(model: BaseLLM) -> None:
    REGISTERED_MODELS[model.model_id] = model


def get_model(model_id: str) -> BaseLLM:
    try:
        return REGISTERED_MODELS[model_id]
    except KeyError as exc:
        raise KeyError(f"Unknown model_id '{model_id}'.") from exc


def list_models() -> list[BaseLLM]:
    return list(REGISTERED_MODELS.values())


def clear_registry() -> None:
    REGISTERED_MODELS.clear()


__all__ = ["register_model", "get_model", "list_models", "clear_registry"]
