"""
Report Generator - Erstellt Markdown Reports aus Evaluation Results
"""
import json
from pathlib import Path
from typing import Optional
from datetime import datetime


class ReportGenerator:
    """Generiert Markdown Reports aus Evaluation Ergebnissen"""
    
    def __init__(self):
        self.results_dir = Path(__file__).parent / "results"
    
    def load_results(self, filename: str = "evaluation_results.json") -> list:
        """Lädt Evaluation Results"""
        filepath = self.results_dir / filename
        with open(filepath) as f:
            return json.load(f)
    
    def generate_summary_table(self, results: list) -> str:
        """Generiert Zusammenfassungs-Tabelle"""
        # Gruppiere nach Modell
        by_model = {}
        for result in results:
            if result.get("error"):
                continue
            model = result["model_id"]
            if model not in by_model:
                by_model[model] = []
            by_model[model].append(result)
        
        lines = ["## Model Comparison\n"]
        lines.append("| Model | Runs | Avg Accuracy | Avg Time | Critical Fields | Passed |")
        lines.append("|-------|------|--------------|----------|-----------------|--------|")
        
        for model_id in sorted(by_model.keys()):
            results_per_model = by_model[model_id]
            total = len(results_per_model)
            
            avg_accuracy = sum(r.get("field_accuracy", 0) for r in results_per_model) / total
            avg_time = sum(r.get("time_ms", 0) for r in results_per_model) / total
            critical_correct = sum(1 for r in results_per_model if r.get("critical_fields_correct")) / total
            schema_valid = sum(1 for r in results_per_model if r.get("schema_valid")) / total
            
            lines.append(
                f"| {model_id} | {total} | {avg_accuracy:.1f}% | {avg_time:.0f}ms | "
                f"{critical_correct*100:.0f}% | {schema_valid*100:.0f}% |"
            )
        
        return "\n".join(lines) + "\n"
    
    def generate_difficulty_breakdown(self, results: list) -> str:
        """Generiert Breakdown nach Schwierigkeit"""
        by_difficulty = {}
        for result in results:
            if result.get("error"):
                continue
            diff = result.get("difficulty", "unknown")
            if diff not in by_difficulty:
                by_difficulty[diff] = []
            by_difficulty[diff].append(result)
        
        lines = ["## Performance by Difficulty\n"]
        lines.append("| Difficulty | Cases | Avg Accuracy | Avg F1 (Missing Fields) |")
        lines.append("|------------|-------|--------------|-------------------------|")
        
        for diff in ["easy", "medium", "hard"]:
            if diff not in by_difficulty:
                continue
            
            results_per_diff = by_difficulty[diff]
            count = len(results_per_diff)
            
            avg_accuracy = sum(r.get("field_accuracy", 0) for r in results_per_diff) / count
            avg_f1 = sum(r.get("missing_fields_f1", 0) for r in results_per_diff) / count
            
            lines.append(
                f"| {diff.capitalize():10} | {count:5} | {avg_accuracy:12.1f}% | {avg_f1:23.2f} |"
            )
        
        return "\n".join(lines) + "\n"
    
    def generate_detailed_results(self, results: list) -> str:
        """Generiert detaillierte Test-Resultate"""
        lines = ["## Detailed Results\n"]
        
        # Gruppiere nach Modell und Test-Case
        by_model_test = {}
        for result in results:
            model = result["model_id"]
            test = result["test_id"]
            key = (model, test)
            by_model_test[key] = result
        
        for model, test in sorted(by_model_test.keys()):
            result = by_model_test[(model, test)]
            
            if result.get("error"):
                lines.append(f"### {model} - {test}")
                lines.append(f"❌ Error: {result['error']}\n")
            else:
                lines.append(f"### {model} - {test}")
                lines.append(f"- **Difficulty**: {result['difficulty']}")
                lines.append(f"- **Accuracy**: {result.get('field_accuracy', 0):.1f}%")
                lines.append(f"- **Schema Valid**: {'✅' if result.get('schema_valid') else '❌'}")
                lines.append(f"- **Critical Fields**: {'✅' if result.get('critical_fields_correct') else '❌'}")
                lines.append(f"- **Missing Fields F1**: {result.get('missing_fields_f1', 0):.2f}")
                lines.append(f"- **Response Time**: {result.get('time_ms', 0):.0f}ms\n")
        
        return "\n".join(lines)
    
    def generate_report(
        self,
        results_file: str = "evaluation_results.json",
        output_file: str = "EVALUATION_REPORT.md"
    ) -> str:
        """Generiert kompletten Report"""
        results = self.load_results(results_file)
        
        markdown = [
            "# LLM Evaluation Report",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Total Test Runs: {len(results)}\n",
            
            "## Overview\n",
            "This report evaluates different LLM models and prompts on their ability to extract",
            "structured insurance claim data from unstructured emails.\n",
            
            "### Metrics Explained\n",
            "- **Accuracy**: Percentage of critical fields correctly extracted",
            "- **Schema Valid**: Output matches the required JSON schema",
            "- **Critical Fields**: Correct identification of has_missing_critical_fields",
            "- **F1 Score**: Balanced metric for missing fields detection (Precision + Recall)\n",
        ]
        
        markdown.append(self.generate_summary_table(results))
        markdown.append(self.generate_difficulty_breakdown(results))
        markdown.append(self.generate_detailed_results(results))
        
        markdown.extend([
            "\n## Conclusion\n",
            "This evaluation demonstrates the effectiveness of different LLM models",
            "in extracting structured data from insurance claim emails.\n",
            
            "- **Best Model**: Determined by average accuracy across all test cases",
            "- **Difficulty Analysis**: Harder cases show the model's capability with incomplete data",
            "- **Schema Compliance**: All models should produce valid JSON output",
        ])
        
        report = "\n".join(markdown)
        
        # Speichere Report
        output_path = self.results_dir / output_file
        with open(output_path, "w") as f:
            f.write(report)
        
        print(f"📄 Report saved to: {output_path}")
        return report


def generate_report():
    """Erzeugt Report aus letzten Ergebnissen"""
    generator = ReportGenerator()
    generator.generate_report()


if __name__ == "__main__":
    generate_report()
