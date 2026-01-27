from __future__ import annotations

import json
import re
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
    def _try_load(payload: str) -> dict[str, Any] | None:
        try:
            return json.loads(payload)
        except json.JSONDecodeError:
            return None

    content = text.strip()
    if not content:
        raise LLMError(empty_error)

    # 1) Plain JSON
    parsed = _try_load(content)
    if parsed is not None:
        return parsed

    # 2) Code-fence wrapped ```json ... ```
    fenced = re.match(r"^```(?:json)?\s*(.*)```$", content, flags=re.DOTALL)
    if fenced:
        parsed = _try_load(fenced.group(1).strip())
        if parsed is not None:
            return parsed

    # 3) Fallback: grab the first {...} block
    start = content.find("{")
    end = content.rfind("}")
    if start != -1 and end != -1 and end > start:
        parsed = _try_load(content[start : end + 1])
        if parsed is not None:
            return parsed

    raise LLMError(f"{provider} returned invalid JSON content")


__all__ = [
    "BuildRequest",
    "FormatError",
    "ParseResponse",
    "ProviderHandler",
    "RequestSpec",
    "format_http_error",
    "parse_json_text",
]
