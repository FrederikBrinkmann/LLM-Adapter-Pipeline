from __future__ import annotations

from textwrap import dedent

SYSTEM_MESSAGE = (
  "You are an expert insurance claims processor. Convert insurance-related emails into "
  "structured JSON tickets with high accuracy. Extract all relevant information, validate "
  "data types, and flag missing critical fields. Your output drives automated ticket creation."
)

JSON_SCHEMA = {
  "name": "insurance_ticket",
  "schema": {
    "type": "object",
    "properties": {
      "ticket_id": {"type": "string"},
      "summary": {"type": "string"},
      "subject": {"type": ["string", "null"]},
      "claimant_name": {"type": ["string", "null"]},
      "claimant_email": {"type": ["string", "null"]},
      "claimant_phone": {"type": ["string", "null"]},
      "description": {"type": ["string", "null"]},
      "priority": {"type": "string", "enum": ["low", "medium", "high", "urgent"]},
      "policy_number": {"type": ["string", "null"]},
      "claim_type": {"type": "string", "enum": ["damage", "medical", "liability", "death", "other"]},
      "claim_date": {"type": ["string", "null"]},
      "incident_date": {"type": ["string", "null"]},
      "incident_location": {"type": ["string", "null"]},
      "claim_amount": {"type": ["number", "null"]},
      "missing_fields": {"type": "array", "items": {"type": "string"}},
      "action_items": {
        "type": "array",
        "items": {
          "oneOf": [
            {"type": "string"},
            {
              "type": "object",
              "properties": {
                "title": {"type": "string"},
                "details": {"type": ["string", "null"]}
              },
              "required": ["title"],
              "additionalProperties": False
            }
          ]
        }
      },
      "next_steps": {"type": "string"},
      "created_timestamp": {"type": "string"},
    },
    "required": ["ticket_id", "summary", "priority", "claim_type", "missing_fields", "action_items", "next_steps"],
    "additionalProperties": False,
  },
}

PROMPT_TEMPLATE = dedent(
  """
  You are processing an insurance claim email into a ticket system. Be precise and extract ALL relevant data.
  
  Return ONLY valid JSON matching this exact schema:
  {
    "ticket_id": "AUTO_GENERATED",
    "summary": string (max 120 chars, clear title),
    "subject": string | null,
    "claimant_name": string | null,
    "claimant_email": string | null,
    "claimant_phone": string | null,
    "description": string | null (detailed summary),
    "priority": "low" | "medium" | "high" | "urgent",
    "policy_number": string | null,
    "claim_type": "damage" | "medical" | "liability" | "death" | "other",
    "claim_date": string | null (YYYY-MM-DD),
    "incident_date": string | null (YYYY-MM-DD),
    "incident_location": string | null,
    "claim_amount": number | null,
    "missing_fields": string[] (critical gaps only),
    "action_items": [string | {title: string, details?: string}] (specific, actionable tasks),
    "next_steps": string (clear instructions for ticket handler),
    "created_timestamp": string (ISO 8601 format)
  }
  
  Processing rules:
  - Extract contact information precisely (name, email, phone).
  - Critical fields to prioritize: claimant_name, policy_number, claim_date, incident_date, claim_type
  - Validate claim_date and incident_date in YYYY-MM-DD format.
  - Set unknown values to null, then add field name to missing_fields.
  - Priority: urgent (life/health risk, > €50k), high (> €10k), medium (standard), low (inquiry).
  - Claim type: must match exactly one enum value.
  - Action items: can be simple strings OR objects with {title, details}. Include details for complex tasks.
  - next_steps: brief instruction for the support team on how to proceed.
  - No comments, no extra keys, valid JSON only.
  
  Email:
  ---
  {email_text}
  ---
  """
)


def build_email_prompt(email_text: str) -> str:
    return PROMPT_TEMPLATE.replace("{email_text}", email_text)


__all__ = ["SYSTEM_MESSAGE", "JSON_SCHEMA", "PROMPT_TEMPLATE", "build_email_prompt"]
