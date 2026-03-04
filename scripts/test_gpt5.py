#!/usr/bin/env python3
"""Debug: Teste GPT-5 direkt mit Pipeline-Prompt."""
import httpx
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("LLM_PIPELINE_OPENAI_API_KEY")

from backend.app.llm.prompting import SYSTEM_MESSAGE, JSON_SCHEMA

test_email = """Sehr geehrte Damen und Herren,
hiermit melde ich einen Wasserschaden in meiner Wohnung.
Am 10.02.2026 ist ein Rohr geplatzt.
Mein Name ist Max Mustermann, Policennummer 123456.
Mit freundlichen Grüßen"""

resp = httpx.post(
    "https://api.openai.com/v1/chat/completions",
    headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    },
    json={
        "model": "gpt-5",
        "messages": [
            {"role": "system", "content": SYSTEM_MESSAGE},
            {"role": "user", "content": test_email},
        ],
        "response_format": {"type": "json_schema", "json_schema": JSON_SCHEMA},
        "max_completion_tokens": 2500,
    },
    timeout=120,
)

print(f"Status: {resp.status_code}")
data = resp.json()
if "error" in data:
    print(f"❌ API Fehler: {data['error']}")
else:
    msg = data.get("choices", [{}])[0].get("message", {})
    content = msg.get("content", "")
    refusal = msg.get("refusal")
    finish_reason = data.get("choices", [{}])[0].get("finish_reason")
    print(f"Finish Reason: {finish_reason}")
    print(f"Refusal: {refusal}")
    print(f"Content length: {len(content) if content else 0}")
    print(f"Content (erste 800 Zeichen):")
    print(content[:800] if content else "(leer)")
