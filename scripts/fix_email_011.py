#!/usr/bin/env python3
"""Generiert den fehlenden Gold-Standard für EMAIL_GEN_011."""

import asyncio
import json
import httpx
from dotenv import load_dotenv
import os

load_dotenv()

SYSTEM_PROMPT = """Du bist ein Experte für Versicherungsschadensmeldungen. Analysiere die E-Mail und extrahiere strukturierte Informationen.

Antworte NUR mit validem JSON in diesem Format:
{
  "subject": "Betreff für das Ticket",
  "summary": "Kurze Zusammenfassung des Schadens",
  "priority": "low" | "medium" | "high" | "critical",
  "claim_type": "auto" | "property" | "liability" | "health" | "life" | "other",
  "action_items": ["Aktion 1", "Aktion 2"],
  "missing_fields": ["Feld das fehlt"],
  "claimant_name": "Name des Versicherungsnehmers",
  "policy_number": "Policennummer falls vorhanden",
  "claim_date": "Datum der Meldung (YYYY-MM-DD)",
  "incident_date": "Datum des Schadens (YYYY-MM-DD)",
  "incident_location": "Ort des Schadens",
  "damage_description": "Beschreibung des Schadens",
  "estimated_amount": "Geschätzte Schadenshöhe als Zahl oder null"
}"""


async def fix_email_011():
    # E-Mails laden
    with open('evaluation/data/synthetic_test_emails.json') as f:
        emails = json.load(f)
    
    # Gold laden
    with open('evaluation/data/synthetic_test_emails_gold.json') as f:
        gold = json.load(f)
    
    # EMAIL_GEN_011 finden
    email = next(e for e in emails['emails'] if e['id'] == 'EMAIL_GEN_011')
    
    print('🔄 Generiere Gold-Standard für EMAIL_GEN_011...')
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            'https://api.openai.com/v1/chat/completions',
            headers={
                'Authorization': f"Bearer {os.getenv('LLM_PIPELINE_OPENAI_API_KEY')}",
                'Content-Type': 'application/json'
            },
            json={
                'model': 'gpt-5.2',
                'max_completion_tokens': 2500,
                'temperature': 0.1,
                'messages': [
                    {'role': 'system', 'content': SYSTEM_PROMPT},
                    {'role': 'user', 'content': email['email_text']}
                ]
            }
        )
        
        data = response.json()
        content = data['choices'][0]['message']['content']
        
        # JSON parsen
        if content.startswith('```'):
            content = content.split('```')[1]
            if content.startswith('json'):
                content = content[4:]
        content = content.strip()
        
        result = json.loads(content)
        print('✅ Erfolgreich!')
        
        # In Gold-Standard einfügen
        found = False
        for i, label in enumerate(gold['labels']):
            if label['id'] == 'EMAIL_GEN_011':
                gold['labels'][i] = {'id': 'EMAIL_GEN_011', 'suggested': result}
                found = True
                break
        
        if not found:
            # An richtiger Stelle einfügen (nach 010, vor 012)
            insert_idx = 10  # Index 10 = 11. Position
            gold['labels'].insert(insert_idx, {'id': 'EMAIL_GEN_011', 'suggested': result})
        
        # Speichern
        with open('evaluation/data/synthetic_test_emails_gold.json', 'w') as f:
            json.dump(gold, f, indent=2, ensure_ascii=False)
        
        print(f'✅ Gold-Standard aktualisiert: {len(gold["labels"])} Labels')


if __name__ == '__main__':
    asyncio.run(fix_email_011())
