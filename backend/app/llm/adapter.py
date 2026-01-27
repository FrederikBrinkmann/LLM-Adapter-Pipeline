from __future__ import annotations

import json
from typing import Any

import httpx

from .base import LLMError
from .prompting import build_email_prompt
from .providers import PROVIDER_HANDLERS


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

        # Log raw Ollama response for debugging JSON parsing issues
        if self.provider == "ollama":
            try:
                raw_text = response.text
                print("OLLAMA RAW RESPONSE (first 2KB):", raw_text[:2000])
            except Exception:
                pass

        try:
            data = response.json()
        except json.JSONDecodeError as exc:  # noqa: B904
            raise LLMError(handler.json_error_message) from exc

        return handler.parse_response(data, self.model_id)


__all__ = ["LLMAdapter", "supports_provider"]
