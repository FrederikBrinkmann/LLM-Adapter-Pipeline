#!/usr/bin/env python3
"""
Generiert einen neuen Gold-Standard basierend auf GPT-5.2.

Usage:
    PYTHONPATH=. python scripts/generate_gold_standard.py
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path

from backend.app.llm.adapter import LLMAdapter
from backend.app.llm.model_config import MODEL_CONFIGS

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

DATA_DIR = Path("evaluation/data")
EMAILS_FILE = DATA_DIR / "synthetic_test_emails.json"
OUTPUT_FILE = DATA_DIR / "synthetic_test_emails_gold.json"

MODEL_ID = "gpt-5.2"


def get_model_config(model_id: str):
    for cfg in MODEL_CONFIGS:
        if cfg.model_id == model_id:
            return cfg
    raise ValueError(f"Model {model_id} not found")


async def generate_gold_label(adapter: LLMAdapter, email_id: str, email_text: str) -> dict:
    """Generiert ein Gold-Label für eine E-Mail."""
    try:
        result = await asyncio.wait_for(
            adapter.generate_structured(text=email_text),
            timeout=180,
        )
        return {
            "id": email_id,
            "status": "ok",
            "suggested": result,
        }
    except Exception as e:
        logger.error(f"  ❌ Fehler bei {email_id}: {e}")
        return {
            "id": email_id,
            "status": "error",
            "error": str(e),
        }


async def main():
    # E-Mails laden
    with open(EMAILS_FILE, encoding="utf-8") as f:
        data = json.load(f)
    emails = data.get("emails", [])
    
    logger.info(f"📧 {len(emails)} E-Mails geladen aus {EMAILS_FILE}")
    logger.info(f"🤖 Verwende Modell: {MODEL_ID}")
    logger.info("")
    
    # Adapter initialisieren
    config = get_model_config(MODEL_ID)
    adapter = LLMAdapter(
        model_id=config.model_id,
        display_name=config.display_name,
        provider=config.provider,
        parameters=config.parameters,
    )
    
    # Labels generieren
    labels = []
    success_count = 0
    
    for i, email in enumerate(emails, 1):
        email_id = email["id"]
        email_text = email["email_text"]
        
        logger.info(f"[{i}/{len(emails)}] {email_id}...")
        
        label = await generate_gold_label(adapter, email_id, email_text)
        labels.append(label)
        
        if label["status"] == "ok":
            success_count += 1
            logger.info(f"  ✅ OK")
        
        # Rate limiting - kurze Pause zwischen Requests
        if i < len(emails):
            await asyncio.sleep(0.5)
    
    # Ergebnis speichern
    output = {
        "generated_at": datetime.now().isoformat(),
        "model": MODEL_ID,
        "total": len(emails),
        "success": success_count,
        "failed": len(emails) - success_count,
        "labels": labels,
    }
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    logger.info("")
    logger.info("=" * 60)
    logger.info(f"✅ Gold-Standard generiert: {OUTPUT_FILE}")
    logger.info(f"   Erfolgreich: {success_count}/{len(emails)}")
    logger.info(f"   Fehlgeschlagen: {len(emails) - success_count}")


if __name__ == "__main__":
    asyncio.run(main())
