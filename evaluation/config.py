"""Zentrale Konfiguration für das Evaluation-Framework."""

from pathlib import Path

# Pfade
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
RESULTS_DIR = BASE_DIR / "results"

# Input-Dateien
EMAILS_FILE = DATA_DIR / "synthetic_test_emails.json"
GOLD_FILE = DATA_DIR / "synthetic_test_emails_gold.json"

# Output-Dateien
RESULTS_FILE = RESULTS_DIR / "evaluation_results.json"
REPORT_FILE = RESULTS_DIR / "EVALUATION_REPORT.md"

# Evaluation Settings
DEFAULT_TIMEOUT_SECONDS = 120  
MAX_CONCURRENT_REQUESTS = 5

# Kritische Felder für Bewertung (alle verglichenen Felder)
CRITICAL_FIELDS = {
    "summary",
    "subject",
    "claimant_name",
    "claimant_email",
    "claimant_phone",
    "description",
    "priority",
    "policy_number",
    "claim_type",
    "claim_date",
    "incident_date",
    "incident_location",
    "claim_amount",
}

# Felder die beim Vergleich ignoriert werden
IGNORE_FIELDS = {
    "ticket_id",
    "created_timestamp",
    "model_id",
}
