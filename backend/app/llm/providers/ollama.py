from __future__ import annotations

from typing import Any

import httpx

from ..config import settings
from ..base import LLMError
from .common import ProviderHandler, RequestSpec, format_http_error, parse_json_text


def _build_request(prompt_text: str, model_id: str, parameters: dict[str, Any]) -> RequestSpec:
    payload: dict[str, Any] = {
        "model": model_id,
        "prompt": prompt_text,
        "stream": False,
    }

    options: dict[str, Any] = {}
    if "temperature" in parameters:
        options["temperature"] = parameters["temperature"]
    if "top_p" in parameters:
        options["top_p"] = parameters["top_p"]
    if "top_k" in parameters:
        options["top_k"] = parameters["top_k"]
    if "max_tokens" in parameters:
        options["num_predict"] = parameters["max_tokens"]

    if options:
        payload["options"] = options

    if "stop" in parameters:
        payload["stop"] = parameters["stop"]

    url = f"{settings.ollama_base_url.rstrip('/')}/api/generate"
    return RequestSpec(url=url, headers={}, payload=payload, timeout=settings.ollama_timeout_seconds)


def _parse_response(data: dict[str, Any], model_id: str) -> dict[str, Any]:
    content = data.get("response")
    if not isinstance(content, str):
        raise LLMError("Ollama response missing text content")

    structured = parse_json_text(
        content,
        provider="Ollama",
        empty_error="Ollama returned an empty response",
    )
    structured.setdefault("model_id", model_id)
    return structured


def _format_error(exc: httpx.HTTPError) -> str:
    return format_http_error("Ollama", exc)


OLLAMA_HANDLER = ProviderHandler(
    build_request=_build_request,
    parse_response=_parse_response,
    format_http_error=_format_error,
    json_error_message="Ollama response was not valid JSON",
)


__all__ = ["OLLAMA_HANDLER"]
