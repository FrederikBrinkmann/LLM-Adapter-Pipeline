#!/usr/bin/env python3
"""Prüft ob Gold-Standard mit aktuellem Datensatz übereinstimmt."""
import json
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "evaluation" / "data"

# Aktuelle E-Mails laden
with open(DATA_DIR / "synthetic_test_emails.json") as f:
    emails = json.load(f)
email_ids = set(item["id"] for item in emails.get("emails", []))

# Gold-Standard aus Archiv laden
gold_path = DATA_DIR / "archive" / "synthetic_test_emails_gold.json"
with open(gold_path) as f:
    gold = json.load(f)
gold_ids = set(item["id"] for item in gold.get("labels", []))

print(f"📧 E-Mails: {len(email_ids)} IDs")
print(f"🏆 Gold-Standard: {len(gold_ids)} IDs")
print()

# Überschneidung
overlap = email_ids & gold_ids
print(f"✅ Übereinstimmend: {len(overlap)}")

# Nur in E-Mails
only_emails = email_ids - gold_ids
if only_emails:
    print(f"⚠️  Nur in E-Mails (kein Gold): {len(only_emails)}")
    print(f"   Beispiele: {sorted(only_emails)[:5]}")

# Nur in Gold
only_gold = gold_ids - email_ids
if only_gold:
    print(f"⚠️  Nur in Gold (keine E-Mail): {len(only_gold)}")
    print(f"   Beispiele: {sorted(only_gold)[:5]}")

# Fazit
print()
if overlap == email_ids == gold_ids:
    print("✅ Gold-Standard und E-Mails stimmen komplett überein!")
elif len(overlap) == 0:
    print("❌ KEIN MATCH! Der Gold-Standard passt nicht zum aktuellen Datensatz.")
    print("   → Du musst einen neuen Gold-Standard generieren.")
else:
    print(f"⚠️  Teilweise Match ({len(overlap)}/{len(email_ids)} E-Mails haben Gold-Labels)")
