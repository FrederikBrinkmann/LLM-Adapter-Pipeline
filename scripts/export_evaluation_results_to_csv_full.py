import json
import csv

json_path = "evaluation/results/evaluation_results.json"
csv_path = "evaluation/results/evaluation_results_export.csv"

FIELDS = [
    "model_id", "email_id", "timestamp", "status", "schema_valid", "field_accuracy", "critical_field_accuracy", "time_ms",
    # Wichtige Felder aus der Modellantwort
    "summary", "description", "claim_type", "claim_amount", "priority", "policy_number", "claim_date", "incident_date", "incident_location",
    # Fehler/Meta
    "missing_fields", "error"
]

with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

results = data["results"]

with open(csv_path, "w", encoding="utf-8", newline='') as f:
    writer = csv.writer(f)
    writer.writerow(FIELDS)
    for r in results:
        row = [
            r.get("model_id", ""),
            r.get("email_id", ""),
            r.get("timestamp", ""),
            r.get("status", ""),
            r.get("schema_valid", ""),
            r.get("field_accuracy", ""),
            r.get("critical_field_accuracy", ""),
            r.get("time_ms", ""),
        ]
        resp = r.get("response", {})
        row.extend([
            resp.get("summary", ""),
            resp.get("description", ""),
            resp.get("claim_type", ""),
            resp.get("claim_amount", ""),
            resp.get("priority", ""),
            resp.get("policy_number", ""),
            resp.get("claim_date", ""),
            resp.get("incident_date", ""),
            resp.get("incident_location", ""),
        ])
        row.append(",".join(resp.get("missing_fields", [])))
        row.append(r.get("error", ""))
        writer.writerow(row)
