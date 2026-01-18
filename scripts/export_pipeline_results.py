#!/usr/bin/env python3
"""Export pipeline job overview and optional ticket submissions."""

from __future__ import annotations

import argparse
import csv
import json
import sqlite3
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = ROOT_DIR / "data" / "pipeline.db"
DEFAULT_OUTPUT_DIR = ROOT_DIR / "evaluation"
DEFAULT_CSV_NAME = "tickets_overview.csv"
DEFAULT_SUMMARY_NAME = "tickets_summary.json"
DEFAULT_SUBMISSION_LOG = "submission_log.json"
DEFAULT_API_BASE = "http://localhost:8000"


@dataclass
class JobRecord:
    job_id: int
    status: str
    model_id: str
    model_display_name: str
    created_at: str
    completed_at: str | None
    submitted_at: str | None
    result: dict[str, Any] | None
    error_message: str | None
    target_status: str | None
    target_reference: str | None


def parse_result(raw: Any) -> dict[str, Any] | None:
    if raw is None:
        return None
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, (bytes, bytearray)):
        raw = raw.decode("utf-8")
    if isinstance(raw, str) and raw.strip():
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None
    return None


def fetch_jobs(db_path: Path) -> list[JobRecord]:
    connection = sqlite3.connect(str(db_path))
    connection.row_factory = sqlite3.Row

    try:
        rows = connection.execute(
            """
            SELECT id, status, model_id, model_display_name,
                   created_at, completed_at, submitted_at,
                   result_json, error_message, target_status, target_reference
            FROM jobs
            ORDER BY id ASC
            """
        ).fetchall()
    finally:
        connection.close()

    records: list[JobRecord] = []
    for row in rows:
        records.append(
            JobRecord(
                job_id=row["id"],
                status=row["status"],
                model_id=row["model_id"],
                model_display_name=row["model_display_name"],
                created_at=row["created_at"],
                completed_at=row["completed_at"],
                submitted_at=row["submitted_at"],
                result=parse_result(row["result_json"]),
                error_message=row["error_message"],
                target_status=row["target_status"],
                target_reference=row["target_reference"],
            )
        )
    return records


def ensure_output_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def build_csv_rows(jobs: list[JobRecord]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for job in jobs:
        result = job.result or {}
        missing_fields = result.get("missing_fields") or []
        if isinstance(missing_fields, list):
            missing_fields = [
                "policy_number" if field == "order_number" else field for field in missing_fields
            ]
        action_items = result.get("action_items") or []
        policy_number = result.get("policy_number") or result.get("order_number")
        claim_amount = result.get("claim_amount")
        claimant_name = result.get("claimant_name") or result.get("customer")
        rows.append(
            {
                "job_id": job.job_id,
                "status": job.status,
                "model_id": job.model_id,
                "model_display_name": job.model_display_name,
                "created_at": job.created_at,
                "completed_at": job.completed_at or "",
                "submitted_at": job.submitted_at or "",
                "summary": result.get("summary", ""),
                "policy_number": policy_number,
                "claim_type": result.get("claim_type"),
                "claim_amount": claim_amount,
                "claimant_name": claimant_name,
                "missing_fields": ", ".join(missing_fields),
                "action_items": "; ".join(action_items),
                "target_status": job.target_status or "",
                "target_reference": job.target_reference or "",
                "error_message": job.error_message or "",
            }
        )
    return rows


def write_csv(rows: list[dict[str, Any]], path: Path) -> None:
    fieldnames = [
        "job_id",
        "status",
        "model_id",
        "model_display_name",
        "created_at",
        "completed_at",
        "submitted_at",
        "summary",
        "policy_number",
        "claim_type",
        "claim_amount",
        "claimant_name",
        "missing_fields",
        "action_items",
        "target_status",
        "target_reference",
        "error_message",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_summary(jobs: list[JobRecord]) -> dict[str, Any]:
    total = len(jobs)
    completed = [job for job in jobs if job.status == "completed" and job.result]
    failed = [job for job in jobs if job.status == "failed"]
    queued = [job for job in jobs if job.status == "queued"]
    in_progress = [job for job in jobs if job.status == "in_progress"]

    ready = [job for job in completed if not (job.result or {}).get("missing_fields")]
    pending = [job for job in completed if (job.result or {}).get("missing_fields")]

    return {
        "total_jobs": total,
        "queued": len(queued),
        "in_progress": len(in_progress),
        "completed": len(completed),
        "failed": len(failed),
        "ready_for_submission": len(ready),
        "pending_information": len(pending),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def submit_job(job_id: int, *, api_base: str) -> dict[str, Any]:
    url = f"{api_base.rstrip('/')}/jobs/{job_id}/submit"
    request = urllib.request.Request(url, data=b"", method="POST")
    request.add_header("Content-Type", "application/json")

    with urllib.request.urlopen(request) as response:  # noqa: S310
        payload = response.read().decode("utf-8")
    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        return {"raw": payload}


def perform_submissions(jobs: list[JobRecord], *, api_base: str) -> list[dict[str, Any]]:
    submissions: list[dict[str, Any]] = []
    for job in jobs:
        result = job.result or {}
        if job.status != "completed":
            continue
        if result.get("missing_fields"):
            continue
        if job.target_status == "submitted":
            continue
        try:
            response = submit_job(job.job_id, api_base=api_base)
            submissions.append(
                {
                    "job_id": job.job_id,
                    "status": "ok",
                    "response": response,
                }
            )
        except urllib.error.HTTPError as exc:
            submissions.append(
                {
                    "job_id": job.job_id,
                    "status": "error",
                    "http_status": exc.code,
                    "reason": exc.reason,
                }
            )
        except urllib.error.URLError as exc:  # type: ignore[misc]
            reason = exc.reason if hasattr(exc, "reason") else str(exc)
            submissions.append(
                {
                    "job_id": job.job_id,
                    "status": "error",
                    "reason": str(reason),
                }
            )
    return submissions


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export pipeline jobs to CSV and submit ready tickets.")
    parser.add_argument("--database", type=Path, default=DEFAULT_DB_PATH, help="Path to pipeline SQLite database")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="Directory for generated reports")
    parser.add_argument("--csv-name", type=str, default=DEFAULT_CSV_NAME, help="Output CSV filename")
    parser.add_argument("--summary-name", type=str, default=DEFAULT_SUMMARY_NAME, help="Output summary JSON filename")
    parser.add_argument("--submit", action="store_true", help="Submit ready tickets via API")
    parser.add_argument("--api-base", type=str, default=DEFAULT_API_BASE, help="Base URL of the pipeline API")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ensure_output_dir(args.output_dir)

    jobs = fetch_jobs(args.database)
    csv_rows = build_csv_rows(jobs)

    csv_path = args.output_dir / args.csv_name
    write_csv(csv_rows, csv_path)

    summary = build_summary(jobs)

    submission_results: list[dict[str, Any]] | None = None
    if args.submit:
        submission_results = perform_submissions(jobs, api_base=args.api_base)
        summary["submitted_now"] = sum(1 for item in submission_results if item.get("status") == "ok")
        summary["submission_errors"] = sum(1 for item in submission_results if item.get("status") == "error")
        log_path = args.output_dir / DEFAULT_SUBMISSION_LOG
        log_path.write_text(json.dumps(submission_results, indent=2), encoding="utf-8")

    summary_path = args.output_dir / args.summary_name
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
