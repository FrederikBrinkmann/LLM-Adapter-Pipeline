"""
Evaluation Metrics für LLM Output Assessment.

Berechnet verschiedene Metriken zum Vergleich von LLM-Outputs mit Gold-Standard.
"""

from typing import Any, Dict, Iterable

from jsonschema import validate, ValidationError

from backend.app.llm.prompting import JSON_SCHEMA
from .config import CRITICAL_FIELDS, IGNORE_FIELDS


class EvaluationMetrics:
    """Berechnet verschiedene Metriken für LLM Output Qualität"""

    # Felder die bei der Schema-Validierung ignoriert werden
    SCHEMA_IGNORE_FIELDS = {"model_id", "next_steps", "action_items"}

    @staticmethod
    def schema_compliance(output: dict) -> tuple[bool, str]:
        """Prüft ob Output dem JSON_SCHEMA entspricht.
        
        Ignoriert model_id (vom System), next_steps und action_items.
        """
        try:
            # Kopie ohne ignorierte Felder für Validierung
            output_clean = {
                k: v for k, v in output.items() 
                if k not in EvaluationMetrics.SCHEMA_IGNORE_FIELDS
            }
            
            # Schema auch anpassen - required Felder ohne die ignorierten
            schema = JSON_SCHEMA.get("schema", JSON_SCHEMA).copy()
            schema = {**schema}  # Deep copy
            if "required" in schema:
                schema["required"] = [
                    f for f in schema["required"] 
                    if f not in EvaluationMetrics.SCHEMA_IGNORE_FIELDS
                ]
            
            validate(instance=output_clean, schema=schema)
            return True, ""
        except ValidationError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Validation error: {str(e)}"

    @staticmethod
    def _iter_comparable_fields(expected: dict, ignore: Iterable[str]) -> Iterable[str]:
        """Liefert die Felder, die für den direkten Vergleich genutzt werden."""
        for field in expected.keys():
            if field in ignore or field == "missing_fields":
                continue
            yield field

    @staticmethod
    def field_accuracy(predicted: dict, expected: dict, ignore: Iterable[str]) -> float:
        """Berechnet % der Felder, die exakt matchen (mit Toleranz für Zahlen)."""
        fields = list(EvaluationMetrics._iter_comparable_fields(expected, ignore))
        if not fields:
            return 0.0

        matches = 0
        for field in fields:
            pred_val = predicted.get(field)
            exp_val = expected.get(field)

            if pred_val == exp_val:
                matches += 1
            elif isinstance(exp_val, (int, float)) and isinstance(pred_val, (int, float)):
                # numerische Toleranz 1%
                if abs(float(pred_val) - float(exp_val)) <= 0.01 * max(abs(float(exp_val)), 1):
                    matches += 1
        return (matches / len(fields)) * 100

    @staticmethod
    def critical_fields_accuracy(predicted: dict, expected: dict) -> float:
        """Accuracy nur über kritische Felder."""
        fields = [f for f in CRITICAL_FIELDS if f in expected]
        if not fields:
            return 0.0
        matches = 0
        for field in fields:
            if predicted.get(field) == expected.get(field):
                matches += 1
        return (matches / len(fields)) * 100

    @staticmethod
    def missing_fields_metrics(predicted: dict, expected: dict) -> Dict[str, float]:
        """Berechnet Precision und Recall für missing_fields Erkennung."""
        pred_missing = set(predicted.get("missing_fields", []))
        exp_missing = set(expected.get("missing_fields", []))

        tp = len(pred_missing & exp_missing)
        fp = len(pred_missing - exp_missing)
        fn = len(exp_missing - pred_missing)

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        return {
            "precision": round(precision, 3),
            "recall": round(recall, 3),
            "f1": round(f1, 3),
        }

    @staticmethod
    def compute_all_metrics(predicted: dict, expected: dict) -> Dict[str, Any]:
        """Berechnet alle Metriken auf einmal."""
        schema_valid, schema_error = EvaluationMetrics.schema_compliance(predicted)
        field_acc = EvaluationMetrics.field_accuracy(predicted, expected, IGNORE_FIELDS)
        critical_acc = EvaluationMetrics.critical_fields_accuracy(predicted, expected)
        missing_metrics = EvaluationMetrics.missing_fields_metrics(predicted, expected)

        return {
            "schema_valid": schema_valid,
            "schema_error": schema_error if not schema_valid else None,
            "field_accuracy": round(field_acc, 1),
            "critical_field_accuracy": round(critical_acc, 1),
            "missing_fields_precision": missing_metrics["precision"],
            "missing_fields_recall": missing_metrics["recall"],
            "missing_fields_f1": missing_metrics["f1"],
        }

    def compute_all(self, predicted: dict, expected: dict) -> Dict[str, Any]:
        """Alias für compute_all_metrics (für Kompatibilität mit runner.py)."""
        return self.compute_all_metrics(predicted, expected)


__all__ = ["EvaluationMetrics"]
