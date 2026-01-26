"""
Evaluation Module - LLM Model & Prompt Comparison Framework

This module provides tools for evaluating different LLM models and prompts
on their ability to extract structured insurance claim data from emails.

Usage:
    python -m evaluation.run_evaluation
    python -m evaluation.generate_report
"""

from evaluation.metrics import EvaluationMetrics
from evaluation.run_evaluation import EvaluationRunner

__all__ = ["EvaluationMetrics", "EvaluationRunner"]
