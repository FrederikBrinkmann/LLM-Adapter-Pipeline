from __future__ import annotations

import json
from textwrap import dedent
from typing import Any

import httpx

from ..config import settings
from .base import BaseLLM, LLMError

PROMPT_TEMPLATE = dedent(
    """
    You are a customer service ticket classifier for e-commerce.
    
    CONTEXT: Extract structured data from customer emails about returns, exchanges, or delivery issues.
    
    INPUT: Customer email text
    OUTPUT: Valid JSON only, no additional text
    
    REQUIRED JSON SCHEMA:
    {
      "summary": string,                      // max 120 chars, captures core issue
      "subject": string | null,               // ticket subject line or null
      "customer": string | null,              // customer name if present
      "description": string | null,           // detailed issue description or null
      "priority": "low" | "medium" | "high" | "urgent",  // MUST be one of these four
      "order_number": string | null,          // order/bestellreferenz or null
      "claim_type": "return" | "exchange" | "delivery_issue" | null,  // MUST be one of these or null
      "missing_fields": string[],             // list only critical missing fields
      "action_items": string[]                // 2-3 specific, actionable next steps
    }
    
    RULES:
    1. Output ONLY valid JSON. No markdown, no explanation.
    2. For unknown values, use null and add field name to missing_fields.
    3. Priority must be exactly one of: low, medium, high, urgent.
    4. claim_type must be exactly one of: return, exchange, delivery_issue, or null.
    5. Action items must be concrete and specific (e.g., "Send return label to customer").
    6. Do not invent data not present in the email.
    
    EMAIL:
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
