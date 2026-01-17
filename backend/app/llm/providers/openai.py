from __future__ import annotations

from typing import Any

import httpx

from ...config import settings
from ..base import LLMError
from ..prompting import JSON_SCHEMA, SYSTEM_MESSAGE
from .common import ProviderHandler, RequestSpec, format_http_error, parse_json_text


def _build_request(prompt_text: str, model_id: str, parameters: dict[str, Any]) -> RequestSpec:
    if not settings.openai_api_key:
        raise LLMError("OpenAI API key is not configured")

    payload: dict[str, Any] = {
        "model": model_id,
        "messages": [
            {"role": "system", "content": SYSTEM_MESSAGE},
            {"role": "user", "content": prompt_text},
        ],
        "response_format": {"type": "json_schema", "json_schema": JSON_SCHEMA},
    }

    temperature = parameters.get("temperature")
    if temperature is not None:
        payload["temperature"] = temperature

    for key in ("top_p", "frequency_penalty", "presence_penalty"):
        value = parameters.get(key)
        if value is not None:
            payload[key] = value

    max_completion_tokens = (
        parameters.get("max_completion_tokens")
        or parameters.get("max_output_tokens")
        or parameters.get("max_tokens")
    )
    if max_completion_tokens is not None:
        payload["max_completion_tokens"] = max_completion_tokens

    stop_sequences = parameters.get("stop")
    if stop_sequences is not None:
        payload["stop"] = stop_sequences

    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }
    url = f"{settings.openai_api_base.rstrip('/')}/chat/completions"
    return RequestSpec(url=url, headers=headers, payload=payload, timeout=settings.openai_timeout_seconds)


def _parse_response(data: dict[str, Any], model_id: str) -> dict[str, Any]:
    try:
        message = data["choices"][0]["message"]
    except (KeyError, IndexError, TypeError) as exc:
        raise LLMError("OpenAI response missing message content") from exc

    content = message.get("content")
    structured: dict[str, Any]

    if isinstance(content, str):
        structured = parse_json_text(
            content,
            provider="OpenAI",
            empty_error="OpenAI returned invalid JSON content",
        )
    elif isinstance(content, list):
        json_payload: dict[str, Any] | None = None
        text_payload: str | None = None

        for part in content:
            if isinstance(part, dict):
                if part.get("type") == "output_text" and "text" in part:
                    text_payload = part["text"]
                elif part.get("type") == "json" and "json" in part:
                    json_payload = part["json"]

        if json_payload is not None:
            structured = json_payload
        elif text_payload is not None:
            structured = parse_json_text(
                text_payload,
                provider="OpenAI",
                empty_error="OpenAI returned invalid JSON content",
            )
        else:
            raise LLMError("OpenAI response did not contain JSON output")
    else:
        raise LLMError("OpenAI response had unexpected content format")

    structured.setdefault("model_id", model_id)
    return structured


def _format_error(exc: httpx.HTTPError) -> str:
    return format_http_error("OpenAI", exc)


OPENAI_HANDLER = ProviderHandler(
    build_request=_build_request,
    parse_response=_parse_response,
    format_http_error=_format_error,
    json_error_message="OpenAI response was not valid JSON",
)


__all__ = ["OPENAI_HANDLER"]
