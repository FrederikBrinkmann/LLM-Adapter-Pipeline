from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable

import httpx

from ..config import settings
from .base import LLMError
from .prompting import JSON_SCHEMA, SYSTEM_MESSAGE, build_email_prompt


@dataclass(frozen=True)
class RequestSpec:
    url: str
    headers: dict[str, str]
    payload: dict[str, Any]
    timeout: float


BuildRequest = Callable[[str, str, dict[str, Any]], RequestSpec]
ParseResponse = Callable[[dict[str, Any], str], dict[str, Any]]
FormatError = Callable[[httpx.HTTPError], str]


@dataclass(frozen=True)
class ProviderHandler:
    build_request: BuildRequest
    parse_response: ParseResponse
    format_http_error: FormatError
    json_error_message: str


def _build_openai_request(prompt_text: str, model_id: str, parameters: dict[str, Any]) -> RequestSpec:
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


def _parse_openai_response(data: dict[str, Any], model_id: str) -> dict[str, Any]:
    try:
        message = data["choices"][0]["message"]
    except (KeyError, IndexError, TypeError) as exc:
        raise LLMError("OpenAI response missing message content") from exc

    content = message.get("content")
    structured: dict[str, Any]

    if isinstance(content, str):
        try:
            structured = json.loads(content)
        except json.JSONDecodeError as exc:  # noqa: B904
            raise LLMError("OpenAI returned invalid JSON content") from exc
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
            try:
                structured = json.loads(text_payload)
            except json.JSONDecodeError as exc:  # noqa: B904
                raise LLMError("OpenAI returned invalid JSON content") from exc
        else:
            raise LLMError("OpenAI response did not contain JSON output")
    else:
        raise LLMError("OpenAI response had unexpected content format")

    structured.setdefault("model_id", model_id)
    return structured


def _format_openai_error(exc: httpx.HTTPError) -> str:
    if isinstance(exc, httpx.HTTPStatusError):
        return (
            f"OpenAI request failed: {exc.response.status_code} "
            f"{exc.response.reason_phrase}: {exc.response.text}"
        )
    return f"OpenAI request failed: {exc}"


def _build_ollama_request(prompt_text: str, model_id: str, parameters: dict[str, Any]) -> RequestSpec:
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


def _parse_ollama_response(data: dict[str, Any], model_id: str) -> dict[str, Any]:
    content = data.get("response")
    if not isinstance(content, str):
        raise LLMError("Ollama response missing text content")

    content = content.strip()
    if not content:
        raise LLMError("Ollama returned an empty response")

    try:
        structured = json.loads(content)
    except json.JSONDecodeError as exc:  # noqa: B904
        raise LLMError("Ollama returned invalid JSON content") from exc

    structured.setdefault("model_id", model_id)
    return structured


def _format_ollama_error(exc: httpx.HTTPError) -> str:
    if isinstance(exc, httpx.HTTPStatusError):
        return (
            f"Ollama request failed: {exc.response.status_code} "
            f"{exc.response.reason_phrase}: {exc.response.text}"
        )
    return f"Ollama request failed: {exc}"


PROVIDER_HANDLERS: dict[str, ProviderHandler] = {
    "openai": ProviderHandler(
        build_request=_build_openai_request,
        parse_response=_parse_openai_response,
        format_http_error=_format_openai_error,
        json_error_message="OpenAI response was not valid JSON",
    ),
    "ollama": ProviderHandler(
        build_request=_build_ollama_request,
        parse_response=_parse_ollama_response,
        format_http_error=_format_ollama_error,
        json_error_message="Ollama response was not valid JSON",
    ),
}


def supports_provider(provider: str) -> bool:
    return provider in PROVIDER_HANDLERS


class LLMAdapter:
    supports_streaming = False

    def __init__(
        self,
        model_id: str,
        display_name: str,
        provider: str,
        *,
        parameters: dict[str, Any] | None = None,
    ) -> None:
        self.model_id = model_id
        self.display_name = display_name
        self.provider = provider
        self.parameters = parameters or {}

    async def generate_structured(self, *, text: str) -> dict[str, Any]:
        handler = PROVIDER_HANDLERS.get(self.provider)
        if handler is None:
            raise LLMError(f"Provider '{self.provider}' is not supported")

        prompt_text = build_email_prompt(text)
        request_spec = handler.build_request(prompt_text, self.model_id, self.parameters)

        async with httpx.AsyncClient(timeout=request_spec.timeout) as client:
            try:
                response = await client.post(
                    request_spec.url,
                    headers=request_spec.headers,
                    json=request_spec.payload,
                )
                response.raise_for_status()
            except httpx.HTTPError as exc:  # noqa: BLE001
                raise LLMError(handler.format_http_error(exc)) from exc

        try:
            data = response.json()
        except json.JSONDecodeError as exc:  # noqa: B904
            raise LLMError(handler.json_error_message) from exc

        return handler.parse_response(data, self.model_id)


__all__ = ["LLMAdapter", "supports_provider"]
