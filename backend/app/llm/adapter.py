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

    async def generate(self, *, prompt: str, system_message: str | None = None) -> dict[str, Any]:
        """
        Generiert eine Antwort ohne strukturiertes Schema.
        Nützlich für freie Text-Generierung wie Follow-up E-Mails.
        """
        from ..config import settings
        
        handler = PROVIDER_HANDLERS.get(self.provider)
        if handler is None:
            raise LLMError(f"Provider '{self.provider}' is not supported")

        # Baue Payload manuell ohne JSON-Schema
        if self.provider == "openai":
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            messages.append({"role": "user", "content": prompt})
            
            payload = {
                "model": self.model_id,
                "messages": messages,
            }
            # Füge optionale Parameter hinzu
            if self.parameters.get("max_completion_tokens"):
                payload["max_completion_tokens"] = self.parameters["max_completion_tokens"]
            
            url = f"{settings.openai_api_base.rstrip('/')}/chat/completions"
            timeout = settings.openai_timeout_seconds
            headers = {
                "Authorization": f"Bearer {settings.openai_api_key}",
                "Content-Type": "application/json",
            }
        else:
            # Ollama
            full_prompt = f"{system_message}\n\n{prompt}" if system_message else prompt
            payload = {
                "model": self.model_id,
                "prompt": full_prompt,
                "stream": False,
            }
            url = f"{settings.ollama_api_base.rstrip('/')}/api/generate"
            timeout = settings.ollama_timeout_seconds
            headers = {}

        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
            except httpx.HTTPError as exc:
                raise LLMError(handler.format_http_error(exc)) from exc

        data = response.json()
        
        # Extrahiere Content
        if self.provider == "openai":
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        else:
            content = data.get("response", "")
        
        return {"content": content}


__all__ = ["LLMAdapter", "supports_provider"]
