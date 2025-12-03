from __future__ import annotations

import json
from textwrap import dedent
from typing import Any

import httpx

from .base import BaseLLM, LLMError
from ..config import settings

PROMPT_TEMPLATE = dedent(
    """
    You turn e-commerce customer emails (returns, exchanges, delivery issues) into strict JSON for a ticket system.
    Return ONLY valid JSON with this shape:
    {
      "summary": string,                      // short title
      "subject": string | null,               // optional, can reuse summary
      "customer": string | null,
      "description": string | null,           // optional short description
      "priority": "low" | "medium" | "high" | "urgent",
      "policy_number": string | null,         // use order number here
      "claim_type": string | null,            // e.g. "return", "exchange", "delivery_issue"
      "missing_fields": string[],             // only real gaps (e.g. "address", "iban", "order_number")
      "action_items": string[]                // concrete next steps
    }

    Rules:
    - Keep summary concise (<=120 chars).
    - If a value is unknown, set it to null and add the field name to missing_fields.
    - Choose priority based on the email’s urgency; must be one of the four enum values.
    - Action items should be actionable, not empty bullet points.
    - No extra keys, no comments.

    Email:
    ---
    {email_text}
    ---
    """
)


class OpenAIAdapter:
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
        self.parameters = parameters or {}
        if not settings.openai_api_key:
            raise LLMError("OpenAI API key is not configured")

    async def generate_structured(self, *, text: str) -> dict:
        prompt_text = PROMPT_TEMPLATE.replace("{email_text}", text)
        payload = {
            "model": self.model_id,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an assistant that converts insurance-related emails into structured JSON outputs following a strict schema.",
                },
                {
                    "role": "user",
                    "content": prompt_text,
                },
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "ecommerce_ticket",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "summary": {"type": "string"},
                            "subject": {"type": ["string", "null"]},
                            "customer": {"type": ["string", "null"]},
                            "description": {"type": ["string", "null"]},
                            "priority": {
                                "type": "string",
                                "enum": ["low", "medium", "high", "urgent"],
                            },
                            "policy_number": {"type": ["string", "null"]},
                            "claim_type": {"type": ["string", "null"]},
                            "missing_fields": {"type": "array", "items": {"type": "string"}},
                            "action_items": {"type": "array", "items": {"type": "string"}},
                        },
                        "required": ["summary", "priority", "missing_fields", "action_items"],
                        "additionalProperties": False,
                    },
                },
            },
        }

        temperature = self.parameters.get("temperature")
        if temperature is not None:
            payload["temperature"] = temperature

        for key in ("top_p", "frequency_penalty", "presence_penalty"):
            value = self.parameters.get(key)
            if value is not None:
                payload[key] = value

        max_completion_tokens = (
            self.parameters.get("max_completion_tokens")
            or self.parameters.get("max_output_tokens")
            or self.parameters.get("max_tokens")
        )
        if max_completion_tokens is not None:
            payload["max_completion_tokens"] = max_completion_tokens

        stop_sequences = self.parameters.get("stop")
        if stop_sequences is not None:
            payload["stop"] = stop_sequences

        headers = {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json",
        }

        url = f"{settings.openai_api_base.rstrip('/')}/chat/completions"

        async with httpx.AsyncClient(timeout=settings.openai_timeout_seconds) as client:
            try:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                detail = exc.response.text
                raise LLMError(
                    f"OpenAI request failed: {exc.response.status_code} {exc.response.reason_phrase}: {detail}"
                ) from exc
            except httpx.HTTPError as exc:  # noqa: BLE001
                raise LLMError(f"OpenAI request failed: {exc}") from exc

        try:
            data = response.json()
        except json.JSONDecodeError as exc:  # noqa: B904
            raise LLMError("OpenAI response was not valid JSON") from exc

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

        structured.setdefault("model_id", self.model_id)
        return structured


__all__ = ["OpenAIAdapter"]
