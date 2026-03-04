"""
Exportiert für jede E-Mail und jedes Modell eine Feldvergleichs-Tabelle (Markdown) zur Nachvollziehbarkeit der Evaluation.
"""
import json
from pathlib import Path
from evaluation.metrics import EvaluationMetrics, SOFT_FIELDS
from evaluation.embedding_utils import embedding_similarity
from evaluation.config import IGNORE_FIELDS

RESULTS_PATH = Path("evaluation/results/evaluation_results.json")
GOLD_PATH = Path("evaluation/data/synthetic_test_emails_gold.json")
EXPORT_DIR = Path("evaluation/results/field_comparisons/")
EXPORT_DIR.mkdir(exist_ok=True)

with open(RESULTS_PATH) as f:
    results = json.load(f)["results"]
with open(GOLD_PATH) as f:
    gold = {l["id"]: l["suggested"] for l in json.load(f)["labels"]}

def compare_field(field, pred, gold):
    if field in SOFT_FIELDS:
        if isinstance(pred, str) and isinstance(gold, str):
            sim = embedding_similarity(pred, gold)
            return f"semantisch ({sim:.2f})", "✅" if sim >= 0.85 else "❌", sim
        return "semantisch", "❌", 0.0
    if pred == gold:
        return "exakt", "✅", 1.0
    if isinstance(pred, (int, float)) and isinstance(gold, (int, float)):
        if abs(float(pred) - float(gold)) <= 0.01 * max(abs(float(gold)), 1):
            return "exakt (Toleranz)", "✅", 1.0
    return "exakt", "❌", 0.0

for entry in results:
    model = entry["model_id"]
    email = entry["email_id"]
    pred = entry["response"]
    gold_entry = gold[email]
    fields = [f for f in gold_entry.keys() if f not in IGNORE_FIELDS]
    md = f"# Feldvergleich: {model} / {email}\n\n| Feld | Gold | LLM | Vergleich | Match | Score |\n|---|---|---|---|---|---|\n"
    for field in fields:
        pred_val = pred.get(field)
        gold_val = gold_entry.get(field)
        cmp, match, score = compare_field(field, pred_val, gold_val)
        md += f"| {field} | {gold_val} | {pred_val} | {cmp} | {match} | {score:.2f} |\n"
    out_path = EXPORT_DIR / f"{model}__{email}.md"
    with open(out_path, "w") as out:
        out.write(md)
