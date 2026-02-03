"""
Evaluation Runner - Testet LLM-Modelle gegen den Gold-Standard.

Usage:
    python -m evaluation.runner                    # Alle Modelle
    python -m evaluation.runner --models gpt-4o    # Einzelnes Modell
    python -m evaluation.runner --limit 10         # Nur 10 E-Mails
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from backend.app.llm.adapter import LLMAdapter
from backend.app.llm.model_config import MODEL_CONFIGS, ModelConfig

from .config import (
    EMAILS_FILE,
    GOLD_FILE,
    RESULTS_DIR,
    RESULTS_FILE,
    DEFAULT_TIMEOUT_SECONDS,
)
from .metrics import EvaluationMetrics

logger = logging.getLogger(__name__)


def get_model_config(model_id: str) -> Optional[ModelConfig]:
    """Holt die ModelConfig für eine model_id."""
    for cfg in MODEL_CONFIGS:
        if cfg.model_id == model_id:
            return cfg
    return None


class EvaluationRunner:
    """Führt Evaluation aller Modelle gegen den Gold-Standard durch."""

    def __init__(self):
        RESULTS_DIR.mkdir(exist_ok=True)
        self.results: list[dict] = []
        self.metrics = EvaluationMetrics()

    def load_emails(self) -> dict[str, str]:
        """Lädt E-Mail-Texte aus JSON."""
        with open(EMAILS_FILE, encoding="utf-8") as f:
            data = json.load(f)
        return {item["id"]: item["email_text"] for item in data.get("emails", [])}

    def load_gold_standard(self) -> dict[str, dict]:
        """Lädt Gold-Standard Labels."""
        with open(GOLD_FILE, encoding="utf-8") as f:
            data = json.load(f)

        gold = {}
        for label in data.get("labels", []):
            if label.get("status") != "ok":
                continue
            if expected := label.get("suggested"):
                gold[label["id"]] = expected
        return gold

    async def evaluate_single(
        self,
        model_id: str,
        email_id: str,
        email_text: str,
        expected: dict,
    ) -> dict:
        """Evaluiert eine einzelne E-Mail mit einem Modell."""
        result = {
            "model_id": model_id,
            "email_id": email_id,
            "timestamp": datetime.now().isoformat(),
        }

        try:
            # ModelConfig für dieses Modell holen
            config = get_model_config(model_id)
            if config is None:
                raise ValueError(f"Unbekanntes Modell: {model_id}")

            adapter = LLMAdapter(
                model_id=config.model_id,
                display_name=config.display_name,
                provider=config.provider,
                parameters=config.parameters,
            )

            start = time.perf_counter()
            response = await asyncio.wait_for(
                adapter.generate_structured(text=email_text),
                timeout=DEFAULT_TIMEOUT_SECONDS,
            )
            elapsed_ms = (time.perf_counter() - start) * 1000

            # Metriken berechnen
            metrics = self.metrics.compute_all(response, expected)

            result.update({
                "status": "success",
                "time_ms": round(elapsed_ms, 1),
                "response": response,
                **metrics,
            })

        except asyncio.TimeoutError:
            result.update({
                "status": "error",
                "error": f"Timeout nach {DEFAULT_TIMEOUT_SECONDS}s",
            })
        except Exception as e:
            logger.exception(f"Fehler bei {model_id}/{email_id}")
            result.update({
                "status": "error",
                "error": str(e),
            })

        return result

    async def run(
        self,
        model_ids: Optional[list[str]] = None,
        limit: Optional[int] = None,
    ) -> list[dict]:
        """
        Führt die komplette Evaluation durch.

        Args:
            model_ids: Liste der zu testenden Modelle (None = alle)
            limit: Maximale Anzahl E-Mails pro Modell (None = alle)
        """
        emails = self.load_emails()
        gold = self.load_gold_standard()

        # Nur E-Mails mit Gold-Standard
        valid_ids = [eid for eid in emails if eid in gold]
        if limit:
            valid_ids = valid_ids[:limit]

        # Modelle bestimmen
        if not model_ids:
            model_ids = [cfg.model_id for cfg in MODEL_CONFIGS]

        total = len(model_ids) * len(valid_ids)
        print(f"🚀 Evaluation: {len(model_ids)} Modelle × {len(valid_ids)} E-Mails = {total} Tests\n")

        current = 0
        for model_id in model_ids:
            print(f"📊 {model_id}")

            for email_id in valid_ids:
                current += 1

                result = await self.evaluate_single(
                    model_id=model_id,
                    email_id=email_id,
                    email_text=emails[email_id],
                    expected=gold[email_id],
                )
                self.results.append(result)

                # Progress
                if result["status"] == "success":
                    acc = result.get("field_accuracy", 0)
                    print(f"   [{current}/{total}] {email_id}: ✅ {acc:.0f}%")
                else:
                    error_msg = result.get("error", "Unknown")[:40]
                    print(f"   [{current}/{total}] {email_id}: ❌ {error_msg}")

        return self.results

    def save_results(self, filepath: Optional[Path] = None) -> None:
        """Speichert Ergebnisse als JSON."""
        filepath = filepath or RESULTS_FILE

        successful = [r for r in self.results if r["status"] == "success"]

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump({
                "generated_at": datetime.now().isoformat(),
                "summary": {
                    "total_tests": len(self.results),
                    "successful": len(successful),
                    "failed": len(self.results) - len(successful),
                },
                "results": self.results,
            }, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Ergebnisse gespeichert: {filepath}")

    def print_summary(self) -> None:
        """Gibt eine Zusammenfassung auf der Konsole aus."""
        if not self.results:
            print("Keine Ergebnisse vorhanden.")
            return

        by_model: dict[str, list] = {}
        for r in self.results:
            by_model.setdefault(r["model_id"], []).append(r)

        print("\n" + "=" * 60)
        print("ZUSAMMENFASSUNG")
        print("=" * 60)

        for model_id in sorted(by_model.keys()):
            rows = by_model[model_id]
            successful = [r for r in rows if r["status"] == "success"]

            if not successful:
                print(f"\n{model_id}: ❌ Alle {len(rows)} Tests fehlgeschlagen")
                continue

            def avg(key: str) -> float:
                vals = [r.get(key) for r in successful if r.get(key) is not None]
                return sum(vals) / len(vals) if vals else 0.0

            schema_valid_count = sum(1 for r in successful if r.get("schema_valid"))
            schema_pct = schema_valid_count / len(successful) * 100

            print(f"\n{model_id}:")
            print(f"  Tests:             {len(successful)}/{len(rows)} erfolgreich")
            print(f"  Field Accuracy:    {avg('field_accuracy'):.1f}%")
            print(f"  Critical Accuracy: {avg('critical_field_accuracy'):.1f}%")
            print(f"  Schema Valid:      {schema_pct:.0f}%")
            print(f"  Avg Time:          {avg('time_ms'):.0f}ms")


async def main() -> None:
    """CLI Entry Point."""
    import argparse

    parser = argparse.ArgumentParser(description="LLM Evaluation Runner")
    parser.add_argument("--models", nargs="+", help="Modelle zum Testen")
    parser.add_argument("--limit", type=int, help="Max E-Mails pro Modell")
    args = parser.parse_args()

    runner = EvaluationRunner()
    await runner.run(model_ids=args.models, limit=args.limit)
    runner.save_results()
    runner.print_summary()


if __name__ == "__main__":
    asyncio.run(main())
