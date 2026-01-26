"""
Evaluation Runner - Testet verschiedene Model/Prompt Kombinationen
"""
import asyncio
import json
import time
from pathlib import Path
from typing import Optional
from datetime import datetime

from backend.app.config import settings
from backend.app.llm.adapter import LLMAdapter
from backend.app.llm.model_config import MODEL_CONFIGS
from backend.app.llm.prompting import build_email_prompt

from evaluation.metrics import EvaluationMetrics


class EvaluationRunner:
    """Führt Evaluation gegen Test-Cases durch"""
    
    def __init__(self):
        self.test_cases_file = Path(__file__).parent / "data" / "test_cases.json"
        self.results_dir = Path(__file__).parent / "results"
        self.results_dir.mkdir(exist_ok=True)
        self.results = []
    
    def load_test_cases(self) -> list:
        """Lädt Test-Cases aus JSON"""
        with open(self.test_cases_file) as f:
            data = json.load(f)
        return data.get("test_cases", [])
    
    async def evaluate_single(
        self,
        model_id: str,
        test_case: dict,
        timeout: int = 30
    ) -> dict:
        """
        Evaluiert ein einzelnes Test-Case gegen Modell
        
        Args:
            model_id: Modell ID (z.B. "gpt-4o-mini")
            test_case: Test-Case Dict mit email + expected
            timeout: Timeout in Sekunden
            
        Returns:
            Ergebnis Dict mit allen Metriken
        """
        result = {
            "test_id": test_case["id"],
            "model_id": model_id,
            "difficulty": test_case.get("difficulty", "unknown"),
            "email_length": len(test_case["email"]),
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Finde Model Config
            model_config = None
            for cfg in MODEL_CONFIGS:
                if cfg.model_id == model_id:
                    model_config = cfg
                    break
            
            if not model_config:
                return {**result, "error": f"Model {model_id} not found in config"}
            
            # Adapter initialisieren
            try:
                model = LLMAdapter(
                    provider=model_config.provider,
                    model_id=model_id,
                    display_name=model_config.display_name
                )
            except Exception as e:
                return {**result, "error": f"Failed to initialize model: {str(e)}"}
            
            # LLM aufrufen mit Timeout
            start_time = time.time()
            try:
                output = await asyncio.wait_for(
                    model.generate_structured(text=test_case["email"]),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                return {**result, "error": f"Timeout after {timeout}s"}
            except Exception as e:
                return {**result, "error": f"LLM call failed: {str(e)}"}
            
            elapsed_time = time.time() - start_time
            result["time_ms"] = round(elapsed_time * 1000, 2)
            
            # Metriken berechnen
            try:
                metrics = EvaluationMetrics.compute_all_metrics(output, test_case["expected"])
                result.update(metrics)
                result["output"] = output  # Für Debugging
            except Exception as e:
                return {**result, "error": f"Metric calculation failed: {str(e)}"}
            
            return result
            
        except Exception as e:
            return {
                **result,
                "error": str(e),
                "output": None
            }
    
    async def run_evaluation(
        self,
        model_ids: Optional[list] = None,
        limit_test_cases: Optional[int] = None
    ) -> list:
        """
        Führt komplette Evaluation durch
        
        Args:
            model_ids: Welche Modelle testen (None = alle verfügbaren)
            limit_test_cases: Limit für Test-Cases (None = alle)
            
        Returns:
            Liste aller Ergebnisse
        """
        test_cases = self.load_test_cases()
        if limit_test_cases:
            test_cases = test_cases[:limit_test_cases]
        
        if not model_ids:
            model_ids = [cfg.model_id for cfg in MODEL_CONFIGS] or ["gpt-4o-mini"]
        
        print(f"🚀 Starting Evaluation")
        print(f"   Models: {model_ids}")
        print(f"   Test Cases: {len(test_cases)}")
        print(f"   Total runs: {len(model_ids) * len(test_cases)}")
        print()
        
        total_runs = len(model_ids) * len(test_cases)
        current_run = 0
        
        for model_id in model_ids:
            print(f"📊 Testing Model: {model_id}")
            
            for test_case in test_cases:
                current_run += 1
                progress = f"[{current_run}/{total_runs}]"
                
                result = await self.evaluate_single(model_id, test_case)
                self.results.append(result)
                
                status = "✅" if not result.get("error") else "❌"
                accuracy = result.get("field_accuracy", "N/A")
                
                print(f"  {progress} {test_case['id']:15} {status} Accuracy: {accuracy}%")
        
        return self.results
    
    def save_results(self, filename: str = "evaluation_results.json"):
        """Speichert Ergebnisse in JSON"""
        filepath = self.results_dir / filename
        with open(filepath, "w") as f:
            json.dump(self.results, f, indent=2)
        print(f"\n💾 Results saved to: {filepath}")
    
    def print_summary(self):
        """Druckt Zusammenfassung"""
        if not self.results:
            print("No results to summarize")
            return
        
        # Gruppiere nach Modell
        by_model = {}
        for result in self.results:
            model = result["model_id"]
            if model not in by_model:
                by_model[model] = []
            by_model[model].append(result)
        
        print("\n" + "="*80)
        print("EVALUATION SUMMARY")
        print("="*80)
        
        for model_id, results in by_model.items():
            valid_results = [r for r in results if not r.get("error")]
            
            if valid_results:
                avg_accuracy = sum(r.get("field_accuracy", 0) for r in valid_results) / len(valid_results)
                avg_time = sum(r.get("time_ms", 0) for r in valid_results) / len(valid_results)
                critical_correct = sum(1 for r in valid_results if r.get("critical_fields_correct")) / len(valid_results)
                
                print(f"\nModel: {model_id}")
                print(f"  ✓ Successful runs: {len(valid_results)}/{len(results)}")
                print(f"  📊 Avg Accuracy: {avg_accuracy:.1f}%")
                print(f"  ⏱️  Avg Time: {avg_time:.0f}ms")
                print(f"  🎯 Critical Fields Correct: {critical_correct*100:.1f}%")
            else:
                print(f"\nModel: {model_id}")
                print(f"  ❌ All runs failed")


async def main():
    """Main Evaluation Script"""
    runner = EvaluationRunner()
    
    # Führe Evaluation durch
    await runner.run_evaluation(
        limit_test_cases=2  # Für schnelles Testing
    )
    
    # Speichere Ergebnisse
    runner.save_results()
    
    # Drucke Zusammenfassung
    runner.print_summary()


if __name__ == "__main__":
    asyncio.run(main())
