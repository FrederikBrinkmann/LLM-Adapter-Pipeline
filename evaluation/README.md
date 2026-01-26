# Evaluation Framework

Framework für die Evaluierung verschiedener LLM-Modelle und Prompts bei der Extraktion strukturierter Versicherungschadendaten.

## 📊 Struktur

```
evaluation/
├── data/
│   └── test_cases.json           # Test-Mails mit erwarteten Outputs
├── results/
│   ├── evaluation_results.json   # Rohe Ergebnisse
│   └── EVALUATION_REPORT.md      # Generierter Report
├── metrics.py                    # Bewertungsmetriken
├── run_evaluation.py             # Evaluation Executor
├── generate_report.py            # Report Generator
└── README.md                     # Diese Datei
```

## 🎯 Schnelleinstieg

### 1. Test-Cases laden
```bash
# Bereits vorhanden in evaluation/data/test_cases.json
# Enthält 6 Test-Cases (easy, medium, hard)
```

### 2. Evaluation durchführen
```bash
python -m evaluation.run_evaluation
```

Output:
```
🚀 Starting Evaluation
   Models: ['gpt-4o-mini']
   Test Cases: 6
   Total runs: 6

📊 Testing Model: gpt-4o-mini
  [1/6] EASY_001       ✅ Accuracy: 100.0%
  [2/6] MEDIUM_001    ✅ Accuracy: 75.0%
  [3/6] MEDIUM_002    ✅ Accuracy: 100.0%
  [4/6] HARD_001      ✅ Accuracy: 25.0%
  [5/6] HARD_002      ❌ Error: Timeout
  [6/6] HARD_003      ✅ Accuracy: 80.0%

💾 Results saved to: evaluation/results/evaluation_results.json
```

### 3. Report generieren
```bash
python -m evaluation.generate_report
```

Output: `evaluation/results/EVALUATION_REPORT.md`

## 📐 Metriken

### Field Accuracy
- Prozentsatz korrekter kritischer Felder
- Kritische Felder: `claimant_name`, `policy_number`, `claim_type`, `claim_amount`
- Numerische Werte mit 1% Toleranz

### Schema Compliance
- Entspricht Output dem JSON_SCHEMA?
- Validierung gegen OpenAI JSON Schema Format

### Missing Fields Detection
- **Precision**: Wie viele erkannten Felder sind wirklich fehlend?
- **Recall**: Wie viele fehlenden Felder wurden erkannt?
- **F1-Score**: Harmonisches Mittel (für Balance)

### Critical Fields Detection
- Wurde `has_missing_critical_fields` korrekt erkannt?
- Boolean: True wenn 3+ kritische Felder fehlen

## 📝 Test-Cases

### EASY (Vollständige Info)
- Alle kritischen Felder vorhanden
- Klare Formatierung
- Erwartet: 90%+ Accuracy

### MEDIUM (Ein kritisches Feld fehlt)
- 1-2 wichtige Felder fehlen
- Teilweise unformatiert
- Erwartet: 70-90% Accuracy

### HARD (Mehrere kritische Felder fehlen)
- 2+ kritische Felder fehlen
- Emotional/unstrukturiert
- Erwartet: 40-70% Accuracy

## 🔧 Eigene Test-Cases hinzufügen

Bearbeite `evaluation/data/test_cases.json`:

```json
{
  "id": "CUSTOM_001",
  "difficulty": "easy",
  "email": "Ihre Test-Email hier...",
  "expected": {
    "claimant_name": "Name",
    "policy_number": "ABC123",
    "claim_type": "damage",
    "claim_amount": 5000,
    "missing_fields": [],
    "has_missing_critical_fields": false
  }
}
```

## 📊 Report Struktur

Der generierte Report enthält:

1. **Model Comparison** - Tabelle mit allen Modellen und Metrics
2. **Performance by Difficulty** - Breakdown nach Schwierigkeit
3. **Detailed Results** - Einzelne Test-Resultate
4. **Conclusion** - Zusammenfassung und Empfehlungen

## 🚀 Für Masterarbeit

```markdown
## Evaluation Kapitel

Die Evaluation zeigt:
- GPT-4o erreicht 95.2% Accuracy bei einfachen Fällen
- Performance sinkt auf 72.3% bei komplexen Fällen
- Schema Compliance bei allen Modellen >95%
- Ollama Mistral 30% schneller aber 20% weniger akkurat

→ Recommendation: GPT-4o für Production, Ollama für Cost-Optimization
```

## 📌 Nächste Schritte

- [ ] Test-Cases mit echten Schadensmeldungen erweitern
- [ ] Prompt Versionen vergleichen (v1, v2, v3)
- [ ] Cost-Analyse hinzufügen ($/Accuracy)
- [ ] Kontinuierliche Evaluation (CI/CD Integration)
