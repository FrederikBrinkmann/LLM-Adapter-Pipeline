"""
Evaluation Metrics für LLM Output Assessment
"""
from typing import Any, Dict
from jsonschema import validate, ValidationError
from backend.app.llm.prompting import JSON_SCHEMA


class EvaluationMetrics:
    """Berechnet verschiedene Metriken für LLM Output Qualität"""
    
    @staticmethod
    def schema_compliance(output: dict) -> tuple[bool, str]:
        """
        Prüft ob Output dem JSON_SCHEMA entspricht
        
        Returns:
            (is_valid, error_message)
        """
        try:
            # Extrahiere das innere schema
            schema = JSON_SCHEMA.get("schema", JSON_SCHEMA)
            validate(instance=output, schema=schema)
            return True, ""
        except ValidationError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    @staticmethod
    def field_accuracy(predicted: dict, expected: dict) -> float:
        """
        Berechnet % der Felder die exakt matchen
        
        Returns:
            Accuracy 0-100
        """
        if not expected:
            return 0.0
        
        critical_fields = ["claimant_name", "policy_number", "claim_type", "claim_amount"]
        
        matches = 0
        for field in critical_fields:
            pred_val = predicted.get(field)
            exp_val = expected.get(field)
            
            # Null values are OK
            if pred_val == exp_val:
                matches += 1
            # Numeric comparison with tolerance
            elif isinstance(exp_val, (int, float)) and isinstance(pred_val, (int, float)):
                if abs(float(pred_val) - float(exp_val)) < 0.01 * float(exp_val):
                    matches += 1
        
        return (matches / len(critical_fields)) * 100
    
    @staticmethod
    def missing_fields_metrics(predicted: dict, expected: dict) -> Dict[str, float]:
        """
        Berechnet Precision und Recall für missing_fields Erkennung
        
        Returns:
            {"precision": float, "recall": float, "f1": float}
        """
        pred_missing = set(predicted.get("missing_fields", []))
        exp_missing = set(expected.get("missing_fields", []))
        
        if not exp_missing:
            # Wenn keine Felder fehlen sollen
            recall = 1.0 if not pred_missing else 0.0
            precision = 1.0 if not pred_missing else 0.0
        else:
            # True Positives: Felder die richtig als fehlend erkannt wurden
            tp = len(pred_missing & exp_missing)
            
            # False Positives: Felder die fälschlich als fehlend erkannt wurden
            fp = len(pred_missing - exp_missing)
            
            # False Negatives: Felder die übersehen wurden
            fn = len(exp_missing - pred_missing)
            
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        
        return {
            "precision": round(precision, 3),
            "recall": round(recall, 3),
            "f1": round(f1, 3)
        }
    
    @staticmethod
    def critical_fields_detection(predicted: dict, expected: dict) -> bool:
        """
        Prüft ob has_missing_critical_fields korrekt erkannt wurde
        
        Returns:
            True wenn Erkennung korrekt, False sonst
        """
        return predicted.get("has_missing_critical_fields") == expected.get("has_missing_critical_fields")
    
    @staticmethod
    def compute_all_metrics(predicted: dict, expected: dict) -> Dict[str, Any]:
        """
        Berechnet alle Metriken auf einmal
        
        Returns:
            Dictionary mit allen Metriken
        """
        schema_valid, schema_error = EvaluationMetrics.schema_compliance(predicted)
        field_acc = EvaluationMetrics.field_accuracy(predicted, expected)
        missing_metrics = EvaluationMetrics.missing_fields_metrics(predicted, expected)
        critical_correct = EvaluationMetrics.critical_fields_detection(predicted, expected)
        
        return {
            "schema_valid": schema_valid,
            "schema_error": schema_error if not schema_valid else None,
            "field_accuracy": round(field_acc, 1),
            "missing_fields_precision": missing_metrics["precision"],
            "missing_fields_recall": missing_metrics["recall"],
            "missing_fields_f1": missing_metrics["f1"],
            "critical_fields_correct": critical_correct
        }


__all__ = ["EvaluationMetrics"]
