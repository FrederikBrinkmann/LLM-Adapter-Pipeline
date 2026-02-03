# LLM Evaluation Report

**Generiert:** 2026-02-03 20:32:15  
**Tests:** 50 (50 erfolgreich, 0 fehlgeschlagen)  
**Modelle:** 5

---

## 📊 Modellvergleich

| Modell | Tests | Field Acc. | Critical Acc. | Schema | Ø Zeit |
|--------|------:|----------:|-------------:|-------:|-------:|
| `gpt-5.2` | 10 | 86.1% | 100.0% | 0% | 11387ms |
| `gpt-4.1` | 10 | 81.5% | 95.0% | 0% | 6915ms |
| `gpt-4.1-mini` | 10 | 77.7% | 91.7% | 0% | 5580ms |
| `gpt-4o` | 10 | 80.0% | 90.0% | 0% | 5562ms |
| `gpt-4o-mini` | 10 | 72.3% | 86.7% | 0% | 5359ms |

---



---

## 🏆 Beste & Schlechteste Ergebnisse

### gpt-4.1

- **Beste:** EMAIL_GEN_011 (85%)
- **Schlechteste:** EMAIL_GEN_002 (77%)

### gpt-4.1-mini

- **Beste:** EMAIL_GEN_011 (85%)
- **Schlechteste:** EMAIL_GEN_005 (69%)

### gpt-4o

- **Beste:** EMAIL_GEN_011 (85%)
- **Schlechteste:** EMAIL_GEN_008 (69%)

### gpt-4o-mini

- **Beste:** EMAIL_GEN_011 (85%)
- **Schlechteste:** EMAIL_GEN_004 (62%)

### gpt-5.2

- **Beste:** EMAIL_GEN_006 (92%)
- **Schlechteste:** EMAIL_GEN_009 (77%)


---

## 📖 Metriken

| Metrik | Beschreibung |
|--------|--------------|
| **Field Acc.** | % der Felder die exakt mit Gold-Standard übereinstimmen |
| **Critical Acc.** | % der *kritischen* Felder (Name, Policy, Datum, Betrag, etc.) |
| **Schema** | Output entspricht dem erwarteten JSON-Schema |
| **Ø Zeit** | Durchschnittliche Antwortzeit in Millisekunden |
