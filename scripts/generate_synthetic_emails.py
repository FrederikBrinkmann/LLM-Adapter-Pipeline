#!/usr/bin/env python3
"""Generate synthetic insurance-related emails for evaluation."""

from __future__ import annotations

import argparse
import json
import random
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Iterable

ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ROOT_DIR / "data" / "emails"
DEFAULT_DATASET_NAME = "synthetic_insurance_emails.jsonl"

CUSTOMER_NAMES = [
    "Alex Bauer",
    "Sandra Klein",
    "Chris Meier",
    "Nina Vogel",
    "Jonas Hoffmann",
    "Lisa Schulz",
    "Felix Roth",
    "Elena Walter",
    "Mark Weber",
    "Julia Koenig",
]

CLAIM_TYPES = [
    "water_damage",
    "theft",
    "accident",
    "liability",
    "fire",
    "storm",
    "glass_breakage",
    "travel",
]

URGENCY_LEVELS = ["low", "medium", "high"]

INCIDENT_LOCATIONS = [
    "Berlin",
    "Munich",
    "Hamburg",
    "Frankfurt",
    "Cologne",
    "Stuttgart",
]

AGENTS = [
    "service@insureme.de",
    "support@secureline.com",
    "claims@fortify-insurance.com",
]

BODY_TEMPLATES = [
    """Hello {agent},\n\nI need to report a {claim_type_label} involving my policy {policy_number}.\nThe incident happened on {incident_date} in {location}. Estimated damage is {loss_estimate}.\nPlease let me know if you need further details or documents.\n\nBest regards,\n{customer_name}\n{phone_hint}""",
    """Hi team,\n\nThis is {customer_name}. I am following up on a {claim_type_label} claim.\nI could not find my policy number, but the loss happened on {incident_date}.\nDamage is around {loss_estimate}. Could you confirm the next steps?\n\nThanks,\n{customer_name}\n{phone_hint}""",
    """Dear insurance support,\n\nI am writing about {claim_type_label}. Policy {policy_number} should cover the incident.\nIt took place near {location} on {incident_date}. I attach photos in the portal.\nThe costs look to be {loss_estimate}.\n\nRegards,\n{customer_name}\n{phone_hint}""",
    """Good morning,\n\nPlease open a new ticket for a {claim_type_label} situation. The event occurred on {incident_date}.\nI believe the policy number is {policy_number}, but please double check.\nDamage is estimated at {loss_estimate}.\n\nThank you,\n{customer_name}\n{phone_hint}""",
    """To whom it may concern,\n\nI want to notify you about {claim_type_label}. I do not have the contract number available right now.\nThe issue happened in {location} on {incident_date}. We expect repair costs of {loss_estimate}.\nLet me know what supporting documents are required.\n\nSincerely,\n{customer_name}\n{phone_hint}""",
]

LOSS_ESTIMATES = [
    "EUR 1,200",
    "EUR 3,500",
    "EUR 7,800",
    "EUR 450",
    "EUR 12,600",
    "EUR 2,350",
]

SUBJECT_TEMPLATES = {
    "water_damage": "Leak in apartment on {incident_date}",
    "theft": "Report of theft on {incident_date}",
    "accident": "Traffic accident claim {incident_date}",
    "liability": "Liability claim raised {incident_date}",
    "fire": "Fire damage notice {incident_date}",
    "storm": "Storm damage from {incident_date}",
    "glass_breakage": "Window glass damage {incident_date}",
    "travel": "Travel insurance issue {incident_date}",
}

CLAIM_LABELS = {
    "water_damage": "water damage claim",
    "theft": "theft claim",
    "accident": "traffic accident",
    "liability": "liability case",
    "fire": "fire damage",
    "storm": "storm damage",
    "glass_breakage": "glass breakage",
    "travel": "travel insurance incident",
}


@dataclass
class SyntheticEmail:
    email_id: str
    subject: str
    body: str
    full_text: str
    metadata: dict[str, str | int | float | None]

    def to_json(self) -> str:
        payload = {
            "email_id": self.email_id,
            "subject": self.subject,
            "body": self.body,
            "full_text": self.full_text,
            "metadata": self.metadata,
        }
        return json.dumps(payload, ensure_ascii=True)


def build_policy_number(rng: random.Random) -> str:
    prefix = rng.choice(["PL", "PN", "IC"])
    digits = "".join(str(rng.randint(0, 9)) for _ in range(7))
    return f"{prefix}-{digits}"


def pick_incident_date(rng: random.Random) -> date:
    start = date.today() - timedelta(days=365)
    offset = rng.randint(0, 364)
    return start + timedelta(days=offset)


def pick_phone_hint(rng: random.Random) -> str:
    if rng.random() < 0.2:
        return ""
    area = rng.randint(200, 999)
    number = rng.randint(1000000, 9999999)
    return f"Phone: +49 {area} {number}"


def generate_email(rng: random.Random, index: int) -> SyntheticEmail:
    customer_name = rng.choice(CUSTOMER_NAMES)
    claim_type = rng.choice(CLAIM_TYPES)
    incident_date = pick_incident_date(rng)
    location = rng.choice(INCIDENT_LOCATIONS)
    loss_estimate = rng.choice(LOSS_ESTIMATES)
    urgency = rng.choice(URGENCY_LEVELS)
    agent = rng.choice(AGENTS)
    policy_number = build_policy_number(rng)

    include_policy = rng.random() > 0.25
    subject = SUBJECT_TEMPLATES[claim_type].format(incident_date=incident_date.isoformat())
    template = rng.choice(BODY_TEMPLATES)
    body = template.format(
        agent=agent,
        claim_type_label=CLAIM_LABELS[claim_type],
        policy_number=policy_number if include_policy else "(unknown)",
        incident_date=incident_date.isoformat(),
        location=location,
        loss_estimate=loss_estimate,
        customer_name=customer_name,
        phone_hint=pick_phone_hint(rng),
    ).strip()

    email_id = f"INS-{index:04d}"
    full_text = f"Subject: {subject}\n\n{body}"

    metadata = {
        "customer_name": customer_name,
        "claim_type": claim_type,
        "policy_number": policy_number if include_policy else None,
        "incident_date": incident_date.isoformat(),
        "location": location,
        "loss_estimate": loss_estimate,
        "urgency": urgency,
        "assigned_agent": agent,
    }

    return SyntheticEmail(email_id=email_id, subject=subject, body=body, full_text=full_text, metadata=metadata)


def write_jsonl(emails: Iterable[SyntheticEmail], path: Path) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for email in emails:
            handle.write(email.to_json())
            handle.write("\n")


def write_individual_files(emails: Iterable[SyntheticEmail], directory: Path) -> None:
    for email in emails:
        file_path = directory / f"{email.email_id}.txt"
        file_path.write_text(email.full_text + "\n", encoding="utf-8")


def ingest_emails(
    emails: Iterable[SyntheticEmail],
    *,
    endpoint: str,
    model_id: str | None,
    limit: int | None,
    pause_seconds: float,
) -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    for index, email in enumerate(emails, start=1):
        if limit is not None and index > limit:
            break

        payload: dict[str, object] = {"text": email.full_text}
        if model_id:
            payload["model_id"] = model_id

        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            endpoint,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        entry: dict[str, object] = {"email_id": email.email_id}
        try:
            with urllib.request.urlopen(request) as response:
                body = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            entry.update({
                "status": "error",
                "http_status": exc.code,
                "reason": exc.reason,
            })
        except urllib.error.URLError as exc:  # type: ignore[misc]
            entry.update({
                "status": "error",
                "reason": str(exc.reason if hasattr(exc, "reason") else exc),
            })
        else:
            try:
                parsed = json.loads(body)
            except json.JSONDecodeError:
                parsed = {"raw": body}

            entry.update({
                "status": "ok",
                "response": parsed,
            })

        results.append(entry)

        if pause_seconds > 0:
            time.sleep(pause_seconds)

    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate synthetic insurance emails for evaluation.")
    parser.add_argument(
        "--count",
        type=int,
        default=200,
        help="Number of emails to generate (default: 200)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=2024,
        help="Random seed for reproducible output",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory to place generated files",
    )
    parser.add_argument(
        "--dataset-name",
        type=str,
        default=DEFAULT_DATASET_NAME,
        help="Name of the JSONL dataset file",
    )
    parser.add_argument(
        "--split",
        action="store_true",
        help="Also write individual .txt files per email",
    )
    parser.add_argument(
        "--ingest-api",
        type=str,
        default=None,
        help="Optional ingest endpoint (e.g. http://localhost:8000/ingest/) to enqueue emails",
    )
    parser.add_argument(
        "--ingest-limit",
        type=int,
        default=None,
        help="Maximum number of emails to send to the ingest endpoint",
    )
    parser.add_argument(
        "--model-id",
        type=str,
        default=None,
        help="Optional model identifier to include in ingest payloads",
    )
    parser.add_argument(
        "--ingest-pause",
        type=float,
        default=0.0,
        help="Seconds to wait between ingest requests",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rng = random.Random(args.seed)

    output_dir: Path = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    emails = [generate_email(rng, index + 1) for index in range(args.count)]

    dataset_path = output_dir / args.dataset_name
    write_jsonl(emails, dataset_path)

    if args.split:
        split_dir = output_dir / "generated"
        split_dir.mkdir(parents=True, exist_ok=True)
        write_individual_files(emails, split_dir)

    ingest_results: list[dict[str, object]] | None = None
    if args.ingest_api:
        ingest_results = ingest_emails(
            emails,
            endpoint=args.ingest_api,
            model_id=args.model_id,
            limit=args.ingest_limit,
            pause_seconds=args.ingest_pause,
        )
        (output_dir / "ingest_results.json").write_text(
            json.dumps(ingest_results, indent=2),
            encoding="utf-8",
        )

    manifest = {
        "count": args.count,
        "dataset_path": str(dataset_path.relative_to(ROOT_DIR)),
        "seed": args.seed,
        "split_files": args.split,
    }

    if args.ingest_api:
        success = sum(1 for item in ingest_results or [] if item.get("status") == "ok")
        manifest.update(
            {
                "ingest_api": args.ingest_api,
                "ingest_limit": args.ingest_limit,
                "ingest_success": success,
                "ingest_errors": len(ingest_results or []) - success,
                "model_id": args.model_id,
                "ingest_pause": args.ingest_pause,
            }
        )

    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
