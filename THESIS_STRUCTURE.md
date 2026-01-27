## LLM-Evaluation für Versicherungs-Email-Verarbeitung

## Kapitel 1: Synthetische Datengenerierung

### 1.1 Literaturgrundlagen
**Was sagt die Literatur?**

- **Wang et al. (2021)**: LLM-generated test sets für NLP-Evaluation
- **He et al. (2023)**: Synthetic data for Named Entity Recognition (direkt relevant!)
- **Zhang et al. (2023)**: Self-Instruct approach für Quality-Datengenerierung
- **Sap et al. (2022)**: Bias in synthetic data (was wir vermeiden müssen!)
- **Debruyne et al. (2023)**: "Synthetic Data, Real Errors" (Limitations)

**Kernerkenntnisse:**
- ✅ LLMs können realistische Testdaten generieren
- ⚠️ Aber: Systematische Biases möglich
- ✅ Quality Control durch Validation erforderlich
- ✅ Dokumentation der Generierungsprozess ist Pflicht

---

### 1.2 Methodologie: Wie haben WIR die Daten erzeugt?

**Ansatz: Nicht Pipeline-optimiert, sondern realitätstreu**

#### 1.2.1 Szenario-Definition
Wir definieren Szenarien **unabhängig von der Pipeline**:

**Schadenstypen (Basis-Szenarien - 5 Kategorien):**
```
1. Wasserschaden (Wohnung/Haus)
2. Autounfall mit Fremdbeteiligung
3. Medizinische Notfall / Krankenhaus
4. Sturmschaden / Naturkalamität
5. Diebstahl / Einbruch
```

**Stimmungen (wie realistisch der Kunde schreiben würde):**
```
1. Ruhig & strukturiert (formell, alle Infos)
2. Gestresst & panisch (unordered, emotional)
3. Wütend & frustriert (Vorwürfe, Konfrontativ)
4. Verwirrt & hilflos (Fragen, unsicher)
5. Geschäftsmäßig (Makler/Rechtsanwalt schreibt)
```

**Information-Level (was der Kunde alles weiß):**
```
1. Vollständig: Hat Policy-Nr, Datum, Betrag, Name
2. Teilweise: Hat Name + 1-2 weitere Infos
3. Minimal: Nur Name oder nur Schadensbeschreibung
4. Vage: Keine konkreten Angaben, nur Problem
```

#### 1.2.2 Prompt-Design
**Kern-Prinzipien:**
- ❌ NICHT: "Generiere strukturierte, einfache Mails"
- ✅ JA: "Generiere realistische Kundenmails wie sie wirklich ankommen"

**Template des Prompts:**
```
[SYSTEM PROMPT]
Du bist ein deutscher Versicherungskunde, der eine Schadensmail schreibt.
Schreibe natürlich, wie ein echter Mensch - mit Fehlern, Unstrukturiertheit, Emotionen.

[SCENARIO-INSTRUCTION]
Szenario: {DAMAGE_TYPE}
Deine Stimmung: {MOOD}
Deine Formalität: {FORMALITY}
Was du weißt: {INFO_LEVEL}

[CONSTRAINTS - für Realismus]
- Schreibe wie ein echter Mensch, nicht wie ein Admin
- Email kann 1-10 Absätze haben
- Verwende realistische Daten (z.B. POL-2025-XXXX)
- Grammatik/Stil variiert je nach Stimmung
- Keine Meta-Tags, keine Strukturhinweise

[OUTPUT]
Nur die Email-Text, nichts anderes.
```

#### 1.2.3 Quality Control
**Akzeptanzkriterien (um Realismus zu sichern):**
```
✅ Ist auf Deutsch
✅ Hat 50-2000 Zeichen
✅ Enthält keine Meta-Tags oder Instructions
✅ Wirkt wie echte Kundenkommunikation
✅ Nicht robot-like oder template-artig

❌ Zu strukturiert (sieht nach Template aus)
❌ Gemischt mit English
❌ Zu kurz oder zu lang
❌ Enthält "generiere", "schreibe", etc.
```

**Metriken:**
```
Generated: X Mails
Accepted: Y Mails
Acceptance Rate: Y/X %

Rejection Breakdown:
- Too structured: ...
- Gemischt English: ...
- Meta-tags present: ...
- Other: ...
```

---

### 1.3 Datensatz-Vorstellung: Kategorien & Struktur

**Dimensionen des Datensatzes:**

Der Datensatz wird durch folgende Dimensionen charakterisiert:

| Dimension | Kategorie | Beschreibung | Anzahl |
|-----------|-----------|-------------|--------|
| **Schadenstyp** | Wasserschaden | Überflutung, Leckage, Wassereintritt | 5 |
| | Autounfall | Verkehrsunfall, Fremdschaden, Karambolage | |
| | Medizinisch | Krankenhaus, medizinische Notfälle, OP | |
| | Sturmschaden | Naturkalamitäten, Dachschaden, Hagelschlag | |
| | Diebstahl | Einbruch, Raub, Diebstahl aus Auto | |
| **Stimmung** | Ruhig & strukturiert | Formell, sachlich, alle Infos sortiert | 5 |
| | Gestresst & panisch | Emotional, unsortiert, Notfall-Gefühl | |
| | Wütend & frustriert | Vorwürfe, Konfrontativ, Beschwerdeton | |
| | Verwirrt & hilflos | Viele Fragen, unsicher, um Hilfe bitte | |
| | Geschäftsmäßig | Makler/Anwalt schreibt, professionell | |
| **Info-Level** | Vollständig | Hat: Name, Policy#, Datum, Betrag, alle kritischen Felder | 4 |
| | Teilweise | Hat: Name + 1-2 weitere Infos, fehlen mehrere kritische | |
| | Minimal | Nur Name oder nur Schadensbeschreibung | |
| | Vage | Keine konkreten Angaben, sehr generisch | |

**Kombinatorik & Datensatz-Umfang:**
```
Schadenstypen (5) × Stimmungen (5) × Info-Levels (4) = 100 Mail-Kombinationen

Zielgröße: 100 Mails (eine pro Kombination)
→ Ermöglicht vollständige systematische Coverage
→ Evaluation kann Breakdowns nach jeder Dimension zeigen
```

**Vorteile dieser Struktur:**
- ✅ Vollständige Coverage aller Kombinationen (keine Lücken)
- ✅ Systematische, reproduzierbare Generierung
- ✅ Evaluation liefert Breakdowns pro Kategorie
- ✅ Einfach zu dokumentieren in der Thesis

---

### 1.4 Datensatz-Beschreibung: Wie sieht der finale Datensatz aus?

**Größe & Verteilung:**
```
Zielgröße: 100 Mails
Struktur: 5 × 5 × 4 = 100 kombinationen

Gleichmäßige Verteilung:
  - Pro Schadenstyp: 20 Mails (alle Stimmung × Info-Level Kombinationen)
  - Pro Stimmung: 20 Mails
  - Pro Info-Level: 25 Mails
```

**Struktur einer Mail im Datensatz:**
```json
{
  "id": "EMAIL_GEN_001",
  "email_text": "Hallo, mein Keller...",
  "generation_metadata": {
    "damage_type": "Wasserschaden",
    "mood": "panisch",
    "formality": "informell",
    "info_level": "teilweise",
    "prompt_template_version": "v1.0",
    "model": "gpt-4o",
    "temperature": 0.9,
    "timestamp": "2026-01-27T..."
  },
  "quality": {
    "accepted": true,
    "realistic_score": 0.92,
    "diversity_tags": ["emotional", "unformatted_date"]
  }
}
```

**Charakteristiken des Datensatzes:**
- ✅ Diverse Schreibstile (formal bis WhatsApp-artig)
- ✅ Verschiedene Längen (1-1000 Worte)
- ✅ Realistische Information-Verteilung (nicht alle Felder vorhanden)
- ✅ Dokumentierte Generierungsmethode
- ✅ Quality-Metriken pro Mail
- ✅ Systematisch konstruiert für vollständige Abdeckung aller Kombinationen

---

### 1.5 Datenverarbeitung: Wie verarbeiten wir die Daten?

**Pipeline:**
```
1. Datengenerierung
   ├─ Generate 100 Mails
   ├─ Quality Filter anwenden
   └─ Accept ~90 Mails

2. Datenbereinigung
   ├─ Formatierung (Whitespace normalisieren)
   ├─ Encoding check (UTF-8)
   └─ Duplikat-Check

3. Persistierung
   ├─ JSON-Format mit Metadaten
   ├─ Backup/Versionierung
   └─ Dokumentation

4. Repräsentativitäts-Check
   ├─ Längen-Verteilung
   ├─ Komplexität-Verteilung
   ├─ Vergleich mit Erwartungen
   └─ Ggf. Nachgenerierung
```

**Output:**
```
evaluation/data/synthetic_test_emails.json
├─ Vollständiger Datensatz mit Metadaten
├─ Generierungsbericht
├─ Quality-Metriken
└─ Dokumentation
```

---

## Evaluationsmethodologie

### 2.1 Evaluation-Konzept

**Ziel:** Verschiedene LLM-Modelle vergleichen bei der Extraktion von Versicherungs-Infos

**Modelle unter Test:**
```
OpenAI:
- GPT-4o (State-of-the-Art)
- GPT-4-turbo (Basis)
- GPT-4o-mini (Schnell & Günstig)

Ollama (lokal):
- Llama 3 (Open-Source)
- Mistral (Open-Source)
```

**Evaluationskriterien:**
```
1. Extraktion-Genauigkeit
   - Stimmen die extrahierten Felder mit erwarteten Werten überein?
   - Metriken: Accuracy, Precision, Recall, F1

2. Schema-Konformität
   - Ist das Output-JSON valide?
   - Sind alle erforderlichen Felder vorhanden?

3. Kritische Felder
   - Wie gut werden WICHTIGE Felder erkannt?
   - (Name, Policy-Nr, Schadenstyp)

4. Fehlerverhalten
   - Welche Fehlertypen tauchen auf?
   - Sind Fehler systematisch oder zufällig?

5. Performance
   - Antwortzeit pro Request
   - API-Kosten
```

---

### 2.2 Aufbau & Konzept

**Multi-Level Evaluation:**

**Level 1: Exact Match**
```
Vergleicht: LLM-Output vs Expected-Output (Feld für Feld)
Beispiel:
  Expected: {"name": "Max Mustermann", "policy": "POL-123"}
  LLM-Output: {"name": "Max Mustermann", "policy": "POL-123"}
  → Match: 100%
```

**Level 2: Schema Compliance**
```
Prüft: Ist das JSON valide? Alle Felder da?
Fehlende Felder zählen als Fehler
```

**Level 3: Critical Fields**
```
Prüft: Wurden KRITISCHE Felder richtig erkannt?
Kritisch: claimant_name, policy_number, claim_type, claim_date
Score: Wie viele der kritischen Felder richtig?
```

**Level 4: Error Pattern Analysis**
```
Kategorisiert Fehler:
- Halluzinationen (erfundene Werte)
- Extraktion misses (hätte erkennen sollen)
- Format-Fehler (z.B. "2025-01-27" statt "27.01.2025")
- Typ-Fehler (string statt number)
```

---

### 2.3 Implementierung (Grob)

**Architektur:**
```
evaluation/
├── data/
│   └── synthetic_test_emails.json      # 100 generierte Mails
├── methods/
│   ├── exact_match.py                   # Level 1
│   ├── schema_validator.py              # Level 2
│   ├── critical_fields.py               # Level 3
│   └── error_analyzer.py                # Level 4
├── run_evaluation.py                    # Haupt-Orchestrator
├── runners/
│   └── model_runner.py                  # Für jedes Modell
└── reporting/
    ├── generate_report.py               # Markdown Report
    └── generate_charts.py               # Visualisierungen
```

**Workflow:**
```
1. Load 100 synthetic emails
2. For each email:
   For each model:
     - Call LLM with extraction prompt
     - Run exact_match check
     - Run schema validation
     - Run critical fields check
     - Record errors
3. Aggregate all results
4. Generate report with tables & charts
```

**Output pro Model:**
```
{
  "model": "gpt-4o",
  "total_emails": 100,
  "results": [
    {
      "email_id": "EMAIL_GEN_001",
      "exact_match_score": 0.85,
      "schema_valid": true,
      "critical_fields_score": 1.0,
      "errors": ["amount_format_mismatch"],
      "response_time_ms": 1250
    },
    ...
  ],
  "aggregated": {
    "avg_exact_match": 0.82,
    "avg_schema_valid": 0.98,
    "avg_critical_fields": 0.88,
    "total_time_ms": 125000,
    "estimated_cost": 0.32
  }
}
```

---

## Kapitel 3: Ergebnisse

### 3.1 Modell-Vergleich
- Tabelle: Alle Modelle, alle Metriken
- Ranking: Best → Worst
- Cost-Performance Trade-off

### 3.2 Fehleranalyse
- Häufigste Fehlertypen
- Systematische Probleme
- Patterns pro Modell

### 3.3 Schwierigkeits-Breakdown
- Welche Szenarien sind für alle Modelle schwierig?
- Wo unterscheiden sich die Modelle?

### 3.4 Conclusio
- Welches Modell empfehlen für Production?
- Trade-offs: Qualität vs. Kosten vs. Latenz
- Limitations & Ausblick

---

## Implementierungs-Roadmap

**Phase 1: Datengenerierung**
- [ ] Szenarien & Stimmungen definieren
- [ ] Prompts schreiben & testen
- [ ] 100 Mails generieren
- [ ] Quality Control
- [ ] Datensatz speichern

**Phase 2: Evaluation-Framework**
- [ ] Exact Match implementieren
- [ ] Schema Validator
- [ ] Critical Fields Checker
- [ ] Error Analyzer
- [ ] Model Runner

**Phase 3: Reporting**
- [ ] Aggregation
- [ ] Markdown Report
- [ ] Charts/Visualisierungen
- [ ] Thesis-ready Output

---
