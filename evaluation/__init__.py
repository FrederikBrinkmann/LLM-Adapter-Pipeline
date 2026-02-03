"""
Evaluation Framework für LLM-Pipeline.

Dieses Modul dient zur systematischen Evaluation verschiedener LLM-Modelle
bei der Extraktion strukturierter Daten aus Versicherungs-E-Mails.

Usage:
    # Synthetische E-Mails generieren (einmalig)
    python -m evaluation.datengenerierung.generate_dataset

    # Evaluation durchführen
    python -m evaluation.runner

    # Report generieren
    python -m evaluation.report
"""

from .config import CRITICAL_FIELDS, IGNORE_FIELDS
from .metrics import EvaluationMetrics
from .runner import EvaluationRunner
from .report import ReportGenerator

__all__ = [
    "EvaluationMetrics",
    "EvaluationRunner",
    "ReportGenerator",
    "CRITICAL_FIELDS",
    "IGNORE_FIELDS",
]
