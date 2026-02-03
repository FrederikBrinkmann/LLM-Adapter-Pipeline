# Evaluation Framework

Dieses Modul dient zur systematischen Evaluation verschiedener LLM-Modelle bei der Extraktion strukturierter Daten aus Versicherungs-E-Mails.

## 📁 Struktur

```
evaluation/
├── __init__.py
├── config.py                    # Zentrale Konfiguration
├── metrics.py                   # Bewertungsmetriken
├── runner.py                    # Evaluation durchführen
├── report.py                    # Report generieren
├── README.md
│
├── datengenerierung/            # Synthetische Testdaten
│   ├── __init__.py
│   └── generate_dataset.py
│
├── data/                        # Input-Daten
│   ├── synthetic_test_emails.json
│   └── synthetic_test_emails_gold.json
│
└── results/                     # Output
    ├── evaluation_results.json
    └── EVALUATION_REPORT.md
```

## 🚀 Nutzung

### 1. Synthetische E-Mails generieren (einmalig)

```bash
python -m evaluation.datengenerierung.generate_dataset
```

### 2. Evaluation durchführen

```bash
# Alle Modelle testen
python -m evaluation.runner

# Nur bestimmte Modelle
python -m evaluation.runner --models gpt-4o claude-3-opus

# Quick-Test mit 10 E-Mails
python -m evaluation.runner --limit 10
```

### 3. Report generieren

```bash
python -m evaluation.report
```

## 📊 Metriken

| Metrik | Beschreibung |
|--------|--------------|
| **Field Accuracy** | % der Felder die exakt mit Gold-Standard übereinstimmen |
| **Critical Accuracy** | Accuracy nur für kritische Felder |
| **Schema Valid** | Output entspricht dem erwarteten JSON-Schema |
| **Time (ms)** | Antwortzeit des Modells |

### Kritische Felder

Die folgenden Felder werden bei der Critical Accuracy besonders bewertet:

- `claimant_name` - Name des Antragstellers
- `policy_number` - Versicherungsnummer
- `claim_type` - Art des Schadens
- `incident_date` - Datum des Vorfalls
- `claim_amount` - Schadenshöhe
- `priority` - Priorität des Tickets

### Missing Fields Erkennung

Zusätzlich wird bewertet, wie gut das Modell fehlende Felder erkennt:

- **Precision** - Wie viele der erkannten fehlenden Felder sind tatsächlich fehlend?
- **Recall** - Wie viele der tatsächlich fehlenden Felder wurden erkannt?
- **F1-Score** - Harmonisches Mittel aus Precision und Recall

## 📄 Output

Der generierte Report (`EVALUATION_REPORT.md`) enthält:

1. **Modellvergleichstabelle** - Alle Modelle sortiert nach Performance
2. **Fehlerübersicht** - Fehlgeschlagene Tests
3. **Beste/Schlechteste Ergebnisse** - Pro Modell
4. **Metrik-Erklärungen**

## 🔧 Konfiguration

Die zentrale Konfiguration befindet sich in `config.py`:

```python
# Timeout für einzelne LLM-Anfragen
DEFAULT_TIMEOUT_SECONDS = 60

# Kritische Felder für Bewertung
CRITICAL_FIELDS = {
    "claimant_name",
    "policy_number",
    "claim_type",
    ...
}

# Felder die beim Vergleich ignoriert werden
IGNORE_FIELDS = {
    "ticket_id",
    "created_timestamp",
    "model_id",
}
```

## 📌 Nächste Schritte

- [ ] Test-Cases mit echten Schadensmeldungen erweitern
- [ ] Prompt Versionen vergleichen (v1, v2, v3)
- [ ] Cost-Analyse hinzufügen ($/Accuracy)
- [ ] Kontinuierliche Evaluation (CI/CD Integration)
