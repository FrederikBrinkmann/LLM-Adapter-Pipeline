from __future__ import annotations

from textwrap import dedent

SYSTEM_MESSAGE = (
    "You are an assistant that converts e-commerce-related emails into structured JSON outputs "
    "following a strict schema."
)

JSON_SCHEMA = {
    "name": "ecommerce_ticket",
    "schema": {
        "type": "object",
        "properties": {
            "summary": {"type": "string"},
            "subject": {"type": ["string", "null"]},
            "customer": {"type": ["string", "null"]},
            "description": {"type": ["string", "null"]},
            "priority": {"type": "string", "enum": ["low", "medium", "high", "urgent"]},
            "order_number": {"type": ["string", "null"]},
            "claim_type": {"type": ["string", "null"]},
            "missing_fields": {"type": "array", "items": {"type": "string"}},
            "action_items": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["summary", "priority", "missing_fields", "action_items"],
        "additionalProperties": False,
    },
}

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
      "order_number": string | null,          // bestellreferenz
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


def build_email_prompt(email_text: str) -> str:
    return PROMPT_TEMPLATE.replace("{email_text}", email_text)


__all__ = ["SYSTEM_MESSAGE", "JSON_SCHEMA", "PROMPT_TEMPLATE", "build_email_prompt"]
