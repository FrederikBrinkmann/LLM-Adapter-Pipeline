"""
Report Generator - Erstellt Markdown-Reports aus Evaluation-Ergebnissen.

Usage:
    python -m evaluation.report
"""

import json
from datetime import datetime
from pathlib import Path

from .config import RESULTS_FILE, REPORT_FILE, RESULTS_DIR


class ReportGenerator:
    """Generiert Markdown-Reports aus Evaluation-Ergebnissen."""

    def __init__(self, results_file: Path = RESULTS_FILE):
        self.results_file = results_file

    def load_results(self) -> dict:
        """Lädt Evaluation-Ergebnisse."""
        with open(self.results_file, encoding="utf-8") as f:
            return json.load(f)

    def generate_model_table(self, results: list[dict]) -> str:
        """Generiert die Hauptvergleichstabelle."""
        by_model: dict[str, list] = {}
        for r in results:
            if r.get("status") == "success":
                by_model.setdefault(r["model_id"], []).append(r)

        lines = [
            "## 📊 Modellvergleich\n",
            "| Modell | Tests | Field Acc. | Critical Acc. | Schema | Ø Zeit |",
            "|--------|------:|----------:|-------------:|-------:|-------:|",
        ]

        def model_score(model_id: str) -> float:
            rows = by_model.get(model_id, [])
            if not rows:
                return 0.0
            vals = [r.get("critical_field_accuracy", 0) for r in rows]
            return sum(vals) / len(vals)

        for model_id in sorted(by_model.keys(), key=model_score, reverse=True):
            rows = by_model[model_id]
            n = len(rows)

            def avg(key: str) -> float:
                vals = [r.get(key) for r in rows if r.get(key) is not None]
                return sum(vals) / len(vals) if vals else 0.0

            field_acc = avg("field_accuracy")
            crit_acc = avg("critical_field_accuracy")
            schema_rate = sum(1 for r in rows if r.get("schema_valid")) / n * 100
            avg_time = avg("time_ms")

            lines.append(
                f"| `{model_id}` | {n} | {field_acc:.1f}% | {crit_acc:.1f}% | {schema_rate:.0f}% | {avg_time:.0f}ms |"
            )

        return "\n".join(lines)

    def generate_error_summary(self, results: list[dict]) -> str:
        """Listet alle Fehler auf."""
        errors = [r for r in results if r.get("status") == "error"]
        if not errors:
            return ""

        lines = [
            "## ❌ Fehler\n",
            "| Modell | E-Mail | Fehler |",
            "|--------|--------|--------|",
        ]

        for r in errors:
            error_msg = r.get("error", "Unknown")[:60]
            lines.append(f"| `{r['model_id']}` | {r['email_id']} | {error_msg} |")

        return "\n".join(lines)

    def generate_best_worst(self, results: list[dict]) -> str:
        """Zeigt beste und schlechteste Ergebnisse pro Modell."""
        by_model: dict[str, list] = {}
        for r in results:
            if r.get("status") == "success":
                by_model.setdefault(r["model_id"], []).append(r)

        lines = ["## 🏆 Beste & Schlechteste Ergebnisse\n"]

        for model_id in sorted(by_model.keys()):
            rows = sorted(
                by_model[model_id],
                key=lambda x: x.get("field_accuracy", 0)
            )

            if len(rows) < 2:
                continue

            worst = rows[0]
            best = rows[-1]

            lines.append(f"### {model_id}\n")
            lines.append(
                f"- **Beste:** {best['email_id']} ({best.get('field_accuracy', 0):.0f}%)"
            )
            lines.append(
                f"- **Schlechteste:** {worst['email_id']} ({worst.get('field_accuracy', 0):.0f}%)"
            )
            lines.append("")

        return "\n".join(lines)

    def generate(self, output_file: Path = REPORT_FILE) -> str:
        """Generiert den kompletten Report."""
        RESULTS_DIR.mkdir(exist_ok=True)

        data = self.load_results()
        results = data.get("results", [])
        summary = data.get("summary", {})

        total_tests = summary.get("total_tests", len(results))
        successful = summary.get("successful", 0)
        failed = summary.get("failed", 0)
        model_count = len(set(r["model_id"] for r in results))

        report = f"""# LLM Evaluation Report

**Generiert:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Tests:** {total_tests} ({successful} erfolgreich, {failed} fehlgeschlagen)  
**Modelle:** {model_count}

---

{self.generate_model_table(results)}

---

{self.generate_error_summary(results)}

---

{self.generate_best_worst(results)}

---

## 📖 Metriken

| Metrik | Beschreibung |
|--------|--------------|
| **Field Acc.** | % der Felder die exakt mit Gold-Standard übereinstimmen |
| **Critical Acc.** | % der *kritischen* Felder (Name, Policy, Datum, Betrag, etc.) |
| **Schema** | Output entspricht dem erwarteten JSON-Schema |
| **Ø Zeit** | Durchschnittliche Antwortzeit in Millisekunden |
"""

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(report)

        print(f"📄 Report generiert: {output_file}")
        return report


def main() -> None:
    """CLI Entry Point."""
    generator = ReportGenerator()
    generator.generate()


if __name__ == "__main__":
    main()
