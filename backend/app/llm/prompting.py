from __future__ import annotations

from textwrap import dedent

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


__all__ = ["PROMPT_TEMPLATE", "build_email_prompt"]
