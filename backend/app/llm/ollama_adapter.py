from __future__ import annotations

import json
from textwrap import dedent
from typing import Any

import httpx

from ..config import settings
from .base import BaseLLM, LLMError

PROMPT_TEMPLATE = dedent(
    """
    You are an assistant that converts insurance-related emails into structured JSON.
    Extract the key details and highlight anything missing. Reply strictly with JSON
    shaped like:
    {
      "model_id": string,
      "summary": string,
      "policy_number": string | null,
      "claim_type": string | null,
      "missing_fields": string[],
      "action_items": string[]
    }

    Guidance:
    - Keep the summary brief (max 3 sentences).
    - Use null for unknown values and list them in "missing_fields".
    - Recommend follow-up steps in "action_items" when helpful.
    - Output must be valid JSON, no additional keys.

    Email:
    ---
    {email_text}
    ---
    """
)


class OllamaAdapter:
    supports_streaming = False

    def __init__(
        self,
        model_id: str,
        display_name: str,
        *,
        parameters: dict[str, Any] | None = None,
    ) -> None:
        self.model_id = model_id
        self.display_name = display_name
        self._base_url = settings.ollama_base_url.rstrip("/")
        self._timeout = settings.ollama_timeout_seconds
        self.parameters = parameters or {}

    async def generate_structured(self, *, text: str) -> dict[str, Any]:
        prompt_text = PROMPT_TEMPLATE.replace("{email_text}", text)

        payload: dict[str, Any] = {
            "model": self.model_id,
            "prompt": prompt_text,
            "stream": False,
        }

        options: dict[str, Any] = {}

        if "temperature" in self.parameters:
            options["temperature"] = self.parameters["temperature"]
        if "top_p" in self.parameters:
            options["top_p"] = self.parameters["top_p"]
        if "top_k" in self.parameters:
            options["top_k"] = self.parameters["top_k"]
        if "max_tokens" in self.parameters:
            options["num_predict"] = self.parameters["max_tokens"]

        if options:
            payload["options"] = options

        if "stop" in self.parameters:
            payload["stop"] = self.parameters["stop"]

        url = f"{self._base_url}/api/generate"

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise LLMError(
                    f"Ollama request failed: {exc.response.status_code} {exc.response.reason_phrase}: {exc.response.text}"
                ) from exc
            except httpx.HTTPError as exc:  # noqa: BLE001
                raise LLMError(f"Ollama request failed: {exc}") from exc

        try:
            data = response.json()
        except json.JSONDecodeError as exc:  # noqa: B904
            raise LLMError("Ollama response was not valid JSON") from exc

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

        structured.setdefault("model_id", self.model_id)
        return structured


__all__ = ["OllamaAdapter"]
