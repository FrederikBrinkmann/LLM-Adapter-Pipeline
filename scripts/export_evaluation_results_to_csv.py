import json
import csv

# Input/Output paths
json_path = "evaluation/results/evaluation_results.json"
csv_path = "evaluation/results/evaluation_results_export.csv"

with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

results = data["results"]

with open(csv_path, "a", encoding="utf-8", newline='') as f:
    writer = csv.writer(f)
    for r in results:
        # Only export successful results
        if r["status"] == "success":
            missing_fields = ",".join(r["response"].get("missing_fields", []))
            writer.writerow([
                r["model_id"],
                r["email_id"],
                r["status"],
                r.get("field_accuracy", ""),
                r.get("critical_field_accuracy", ""),
                r.get("time_ms", ""),
                missing_fields
            ])
