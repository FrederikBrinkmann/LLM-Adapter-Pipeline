#!/usr/bin/env python3
"""
Synthetische Datensatz-Generierung für Thesis-Evaluation.

Generiert 100 realistische Versicherungs-Kundenmails durch systematische
Kombination von Szenarien (5) × Stimmungen (5) × Information-Levels (4).

Struktur:
  - CONFIG: Alle Parameter hier änderbar
  - Scenarios: Definition der 5×5×4 Dimensionen
  - Generierung: Prompt-Building + LLM-Call
  - Quality Control: Validierung
  - Output: JSON mit Metadaten
"""

import json
import asyncio
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Optional
from pathlib import Path

import openai
from openai import AsyncOpenAI

# ============================================================================
# CONFIG - Hier Parameter ändern!
# ============================================================================

class CONFIG:
    """Alle Konfigurationsparameter."""
    
    # LLM Settings
    MODEL = "gpt-4o"
    TEMPERATURE = 0.9  # Höher = mehr Variation
    MAX_TOKENS = 1000
    
    # Datensatz-Größe
    DAMAGE_TYPES = [
        "Wasserschaden",
        "Autounfall",
        "Medizinisch",
        "Sturmschaden",
        "Diebstahl",
    ]
    
    MOODS = [
        "ruhig und strukturiert",
        "gestresst und panisch",
        "wütend und frustriert",
        "verwirrt und hilflos",
        "geschäftsmäßig",
    ]
    
    INFO_LEVELS = [
        "vollständig",
        "teilweise",
        "minimal",
        "vage",
    ]
    
    # Output
    OUTPUT_DIR = Path(__file__).parent / "data"
    OUTPUT_FILE = OUTPUT_DIR / "synthetic_test_emails.json"
    
    # Quality Control
    MIN_CHARS = 50
    MAX_CHARS = 2000
    ACCEPTANCE_RATE_TARGET = 0.85
    
    # Logging
    VERBOSE = True


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class SyntheticEmail:
    """Eine generierte Email mit Metadaten."""
    
    id: str
    email_text: str
    generation_metadata: dict
    quality: dict
    
    def to_dict(self):
        """Für JSON-Serialisierung."""
        return asdict(self)


# ============================================================================
# SCENARIO DESCRIPTIONS - Was ist ein "Wasserschaden"?
# ============================================================================

SCENARIO_DESCRIPTIONS = {
    "Wasserschaden": {
        "description": "Überflutung, Wassereintritt, Rohrbruch",
        "examples": ["Keller geflutet", "Wohnung unter Wasser", "Leckage vom Nachbarn"],
        "typical_amount": "5.000 - 50.000 EUR",
    },
    "Autounfall": {
        "description": "Verkehrsunfall mit Fremdbeteiligung, Karambolage",
        "examples": ["Auffahrunfall", "Seitencrash", "Parkplatzschaden"],
        "typical_amount": "2.000 - 100.000 EUR",
    },
    "Medizinisch": {
        "description": "Krankenhaus, medizinische Notfälle, Operation",
        "examples": ["Notfall-OP", "Krankenhaus-Aufenthalt", "Zahnbehandlung"],
        "typical_amount": "1.000 - 50.000 EUR",
    },
    "Sturmschaden": {
        "description": "Naturkalamitäten, Dachschaden, Hagelschlag",
        "examples": ["Sturm riss Dach ab", "Hagelschaden Auto", "Baum fiel auf Haus"],
        "typical_amount": "1.000 - 100.000 EUR",
    },
    "Diebstahl": {
        "description": "Einbruch, Raub, Diebstahl aus Auto",
        "examples": ["Wohnung eingebrochen", "Auto aufgebrochen", "Handtasche geklaut"],
        "typical_amount": "500 - 30.000 EUR",
    },
}

MOOD_DESCRIPTIONS = {
    "ruhig und strukturiert": "Formell, sachlich, gut organisiert, alle Infos sortiert",
    "gestresst und panisch": "Emotional, durcheinander, CAPS LOCK, viele !!!, Notfall-Feeling",
    "wütend und frustriert": "Vorwürfe, Konfrontativ, Beschwerdeton, Sarkasmus",
    "verwirrt und hilflos": "Viele Fragen, unsicher, um Hilfe bitte, verloren",
    "geschäftsmäßig": "Makler/Anwalt schreibt, professionell, formale Struktur",
}

INFO_LEVEL_DESCRIPTIONS = {
    "vollständig": "Hat: Name, Policy-Nummer, Schadendatum, Betrag - ALLE kritischen Infos",
    "teilweise": "Hat: Name + 1-2 weitere Infos - MEHRERE kritische Felder fehlen",
    "minimal": "Hat: Nur Name ODER nur Schadensbeschreibung - WENIGE konkrete Infos",
    "vage": "Hat: KEINE konkreten Angaben - sehr generisch, keine Daten",
}


# ============================================================================
# PROMPT-BUILDING
# ============================================================================

def build_prompt(
    damage_type: str,
    mood: str,
    info_level: str,
) -> str:
    """Baut den Prompt für die Mail-Generierung."""
    
    scenario_desc = SCENARIO_DESCRIPTIONS[damage_type]
    mood_desc = MOOD_DESCRIPTIONS[mood]
    info_desc = INFO_LEVEL_DESCRIPTIONS[info_level]
    
    prompt = f"""Du bist ein deutscher Versicherungskunde und schreibst eine Schadensmail.

SZENARIO:
Schadenstyp: {damage_type}
Beschreibung: {scenario_desc['description']}
Typische Schadenshöhe: {scenario_desc['typical_amount']}

DEINE CHARAKTERISTIKA:
Stimmung: {mood}
  → {mood_desc}
Information-Level: {info_level}
  → {info_desc}

WICHTIG - REALISMUS:
- Schreibe wie ein echter Mensch würde, nicht wie ein Admin oder Formular
- Grammatik und Stil sollen zu deiner Stimmung passen
- Die Email kann 1-15 Absätze haben
- Verwende realistische Daten: Namen, Versicherungsnummern (Format: POL-2025-XXXX), Telefonnummern
- Wenn dein Info-Level "vage" ist: Schreibe bewusst wenig konkrete Infos
- Keine Meta-Tags, keine Struktur-Hinweise, keine Erklärungen
- Typos und Fehler sind OK (je nach Stimmung)

CONSTRAINTS:
- Die Email muss zwischen 50 und 2000 Zeichen lang sein
- Keine Anrede wie "Sehr geehrte Damen und Herren" für "panisch", aber OK für "strukturiert"
- Keine doppelten Ausrufezeichen wenn nicht emotional

AUSGABE:
Nur die Email-Text, NICHTS anderes. Keine Metadaten, keine Erklärungen.
"""
    
    return prompt


# ============================================================================
# LLM CALL
# ============================================================================

async def generate_email(
    damage_type: str,
    mood: str,
    info_level: str,
    client: AsyncOpenAI,
) -> tuple[str, dict]:
    """Generiert eine Mail via GPT-4o."""
    
    prompt = build_prompt(damage_type, mood, info_level)
    
    try:
        response = await client.chat.completions.create(
            model=CONFIG.MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "Du bist ein realistischer Versicherungskunde.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=CONFIG.TEMPERATURE,
            max_tokens=CONFIG.MAX_TOKENS,
        )
        
        email_text = response.choices[0].message.content.strip()
        
        return email_text, {"success": True, "tokens_used": response.usage.total_tokens}
    
    except Exception as e:
        return None, {"success": False, "error": str(e)}


# ============================================================================
# QUALITY CONTROL
# ============================================================================

def is_realistic_email(email_text: Optional[str]) -> tuple[bool, dict]:
    """Validiert, ob die Mail realistisch ist."""
    
    issues = []
    
    # Basic Checks
    if not email_text:
        issues.append("Email ist None")
        return False, {"issues": issues}
    
    if len(email_text) < CONFIG.MIN_CHARS:
        issues.append(f"Zu kurz: {len(email_text)} < {CONFIG.MIN_CHARS}")
    
    if len(email_text) > CONFIG.MAX_CHARS:
        issues.append(f"Zu lang: {len(email_text)} > {CONFIG.MAX_CHARS}")
    
    # Content Checks
    if "<EMAIL>" in email_text or "[EMAIL]" in email_text:
        issues.append("Enthält Meta-Tags")
    
    if "generiere" in email_text.lower() or "schreibe" in email_text.lower():
        issues.append("Enthält Prompt-Artifacts")
    
    if email_text.count("\n\n") > 20:
        issues.append("Zu viele Absätze")
    
    # German Check (sehr einfach)
    german_words = ["und", "der", "die", "das", "ich", "eine"]
    has_german = sum(1 for word in german_words if word in email_text.lower())
    if has_german < 2:
        issues.append("Vermutlich nicht auf Deutsch")
    
    is_valid = len(issues) == 0
    
    return is_valid, {
        "accepted": is_valid,
        "issues": issues,
        "char_count": len(email_text),
        "realistic_score": 1.0 if is_valid else 0.0,
    }


# ============================================================================
# MAIN GENERATION
# ============================================================================

async def generate_all_emails() -> list[SyntheticEmail]:
    """Generiert alle 100 Kombinationen."""
    
    client = AsyncOpenAI()
    emails = []
    accepted = 0
    rejected = 0
    
    print(f"Starte Datengenerierung...")
    print(f"Ziel: {len(CONFIG.DAMAGE_TYPES)} × {len(CONFIG.MOODS)} × {len(CONFIG.INFO_LEVELS)} = {len(CONFIG.DAMAGE_TYPES) * len(CONFIG.MOODS) * len(CONFIG.INFO_LEVELS)} Emails")
    print()
    
    email_id = 0
    
    for damage_type in CONFIG.DAMAGE_TYPES:
        for mood in CONFIG.MOODS:
            for info_level in CONFIG.INFO_LEVELS:
                email_id += 1
                
                # Generierung
                email_text, gen_meta = await generate_email(
                    damage_type, mood, info_level, client
                )
                
                # Quality Control
                is_valid, quality_meta = is_realistic_email(email_text)
                
                if is_valid:
                    accepted += 1
                    status = "✅"
                else:
                    rejected += 1
                    status = "❌"
                
                if CONFIG.VERBOSE:
                    print(
                        f"{status} [{email_id:3d}] {damage_type:12} | {mood:20} | {info_level:12} "
                        f"| {quality_meta['char_count']:4d} chars"
                    )
                
                # Speichern (auch rejected, zur Dokumentation)
                email_obj = SyntheticEmail(
                    id=f"EMAIL_GEN_{email_id:03d}",
                    email_text=email_text or "[GENERATION FAILED]",
                    generation_metadata={
                        "damage_type": damage_type,
                        "mood": mood,
                        "info_level": info_level,
                        "model": CONFIG.MODEL,
                        "temperature": CONFIG.TEMPERATURE,
                        **gen_meta,
                    },
                    quality=quality_meta,
                )
                
                emails.append(email_obj)
                
                # Rate limiting
                await asyncio.sleep(0.1)
    
    print()
    print(f"Generierung abgeschlossen!")
    print(f"  Akzeptiert: {accepted}/{email_id} ({100*accepted/email_id:.1f}%)")
    print(f"  Rejected: {rejected}/{email_id}")
    
    return emails


# ============================================================================
# OUTPUT
# ============================================================================

def save_dataset(emails: list[SyntheticEmail]) -> None:
    """Speichert den Datensatz als JSON."""
    
    CONFIG.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Dataset mit Statistiken
    dataset = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "total_emails": len(emails),
            "accepted_emails": sum(1 for e in emails if e.quality["accepted"]),
            "model": CONFIG.MODEL,
            "temperature": CONFIG.TEMPERATURE,
            "scenarios": {
                "damage_types": CONFIG.DAMAGE_TYPES,
                "moods": CONFIG.MOODS,
                "info_levels": CONFIG.INFO_LEVELS,
            },
        },
        "emails": [e.to_dict() for e in emails],
    }
    
    with open(CONFIG.OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Datensatz gespeichert: {CONFIG.OUTPUT_FILE}")
    print(f"   Größe: {CONFIG.OUTPUT_FILE.stat().st_size / 1024:.1f} KB")


# ============================================================================
# CLI
# ============================================================================

async def main():
    """Haupteinstieg."""
    
    print("=" * 80)
    print("SYNTHETISCHE DATENSATZ-GENERIERUNG")
    print("=" * 80)
    print(f"Model: {CONFIG.MODEL}")
    print(f"Temperature: {CONFIG.TEMPERATURE}")
    print(f"Output: {CONFIG.OUTPUT_FILE}")
    print("=" * 80)
    print()
    
    emails = await generate_all_emails()
    save_dataset(emails)
    
    print()
    print("=" * 80)
    print("✅ FERTIG!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
