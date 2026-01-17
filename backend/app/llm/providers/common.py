from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable

import httpx

from ..base import LLMError


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


def format_http_error(provider: str, exc: httpx.HTTPError) -> str:
    if isinstance(exc, httpx.HTTPStatusError):
        return (
            f"{provider} request failed: {exc.response.status_code} "
            f"{exc.response.reason_phrase}: {exc.response.text}"
        )
    return f"{provider} request failed: {exc}"


def parse_json_text(text: str, *, provider: str, empty_error: str) -> dict[str, Any]:
    content = text.strip()
    if not content:
        raise LLMError(empty_error)
    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:  # noqa: B904
        raise LLMError(f"{provider} returned invalid JSON content") from exc


__all__ = [
    "BuildRequest",
    "FormatError",
    "ParseResponse",
    "ProviderHandler",
    "RequestSpec",
    "format_http_error",
    "parse_json_text",
]
