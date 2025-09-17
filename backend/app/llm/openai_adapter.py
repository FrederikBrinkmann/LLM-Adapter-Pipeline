from __future__ import annotations

import json
from textwrap import dedent
from typing import Any

import httpx

from .base import BaseLLM, LLMError
from ..config import settings

PROMPT_TEMPLATE = dedent(
    """
    You are an assistant that converts insurance-related emails into structured JSON.
    Extract the key information and highlight missing essentials. Return **only** valid JSON
    with the following shape:
    {
      "model_id": string,
      "summary": string,
      "policy_number": string | null,
      "claim_type": string | null,
      "missing_fields": string[],
      "action_items": string[]
    }

    Rules:
    - Keep summary concise (max 3 sentences).
    - If a field is unknown, use null and mention it in "missing_fields".
    - "missing_fields" should only include keys that truly lack information.
    - Provide actionable follow-up steps in "action_items" (empty list if none).
    - Do not add extra keys.

    Email:
    ---
    {email_text}
    ---
    """
)


class OpenAIAdapter:
    supports_streaming = False

    def __init__(self, model_id: str, display_name: str) -> None:
        self.model_id = model_id
        self.display_name = display_name
        if not settings.openai_api_key:
            raise LLMError("OpenAI API key is not configured")

    async def generate_structured(self, *, text: str) -> dict:
        prompt_text = PROMPT_TEMPLATE.replace("{email_text}", text)
        payload = {
            "model": self.model_id,
            "temperature": 0,
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
                    "name": "insurance_ticket",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "model_id": {"type": "string"},
                            "summary": {"type": "string"},
                            "policy_number": {"type": ["string", "null"]},
                            "claim_type": {"type": ["string", "null"]},
                            "missing_fields": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "action_items": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                        },
                        "required": [
                            "model_id",
                            "summary",
                            "policy_number",
                            "claim_type",
                            "missing_fields",
                            "action_items",
                        ],
                        "additionalProperties": False,
                    },
                },
            },
        }

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
