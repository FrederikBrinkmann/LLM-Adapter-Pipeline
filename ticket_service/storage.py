from __future__ import annotations

import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from .schemas import ActionItem, ActionItemCreate, Ticket, TicketCreate, TicketStatus, TicketUpdate

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "tickets_store.json"
DATA_PATH.parent.mkdir(parents=True, exist_ok=True)


class TicketNotFoundError(Exception):
    pass


class TicketStore:
    def __init__(self, path: Path = DATA_PATH) -> None:
        self.path = path
        self._lock = threading.Lock()
        self._data: dict[str, Any] = {"next_id": 1, "tickets": []}
        file_existed = self.path.exists()
        self._load()
        if not self._data["tickets"] and not file_existed:
            self._seed()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            payload = json.loads(self.path.read_text())
            if isinstance(payload, dict):
                self._data.update(payload)
                changed = False
                for ticket in self._data.get("tickets", []):
                    if not isinstance(ticket, dict):
                        continue
                    if "policy_number" not in ticket and "order_number" in ticket:
                        ticket["policy_number"] = ticket.pop("order_number")
                        changed = True
                    if "claimant_name" not in ticket and "customer" in ticket:
                        ticket["claimant_name"] = ticket.pop("customer")
                        changed = True
                    missing_fields = ticket.get("missing_fields")
                    if isinstance(missing_fields, list):
                        updated_missing = [
                            "policy_number" if field == "order_number" else field for field in missing_fields
                        ]
                        if updated_missing != missing_fields:
                            ticket["missing_fields"] = updated_missing
                            changed = True
                if changed:
                    self._persist()
        except json.JSONDecodeError:
            self._data = {"next_id": 1, "tickets": []}

    def _persist(self) -> None:
        serialized = json.dumps(self._data, indent=2)
        self.path.write_text(serialized)

    def _seed(self) -> None:
        now = datetime.utcnow().isoformat()
        samples = [
            {
                "id": 1,
                "ticket_id": "CLM-0001",
                "subject": "Wasserschaden im Keller",
                "summary": "Schaden nach Starkregen, Wasser im Keller gemeldet.",
                "claimant_name": "Familie König",
                "claimant_email": "koenig@example.com",
                "claimant_phone": "+49 221 555 123",
                "description": "Keller nach Unwetter geflutet, Kunde bittet um schnelle Hilfe.",
                "priority": "urgent",
                "status": TicketStatus.TODO.value,
                "policy_number": "HZ-88923",
                "claim_type": "damage",
                "claim_date": "2025-01-12",
                "incident_date": "2025-01-11",
                "incident_location": "Köln",
                "claim_amount": 18000,
                "missing_fields": ["damage_estimate", "photos"],
                "has_missing_critical_fields": False,
                "action_items": [
                    {
                        "id": self._generate_action_id(),
                        "title": "Gutachter zuweisen",
                        "details": "Partnerdienstleister in Köln informieren",
                        "suggested_by": "agent",
                        "status": "open",
                    }
                ],
                "next_steps": "Schaden aufnehmen, Gutachtertermin koordinieren, erste Zahlung prüfen.",
                "created_timestamp": "2025-01-12T08:10:00Z",
                "source_job_id": None,
                "source_model_id": None,
                "raw_payload": None,
                "created_at": now,
                "updated_at": now,
            },
            {
                "id": 2,
                "ticket_id": "CLM-0002",
                "subject": "Sturzverletzung nach Treppensturz",
                "summary": "Kunde meldet Sturz mit Armverletzung, Arztbericht fehlt.",
                "claimant_name": "Max Mustermann",
                "claimant_email": "max.mustermann@example.com",
                "claimant_phone": "+49 151 234 5678",
                "description": "Unfall beim Treppenabstieg, Verdacht auf Fraktur.",
                "priority": "high",
                "status": TicketStatus.IN_PROGRESS.value,
                "policy_number": "UNF-77210",
                "claim_type": "medical",
                "claim_date": "2025-01-10",
                "incident_date": "2025-01-09",
                "incident_location": "Hamburg",
                "claim_amount": 6500,
                "missing_fields": ["medical_report"],
                "has_missing_critical_fields": False,
                "action_items": [
                    {
                        "id": self._generate_action_id(),
                        "title": "Unterlagen anfordern",
                        "details": "Arztbericht und Rechnung vom Kunden einholen",
                        "suggested_by": "llm",
                        "status": "open",
                    }
                ],
                "next_steps": "Medizinische Unterlagen prüfen, Anspruchsvoraussetzungen klären.",
                "created_timestamp": "2025-01-10T15:45:00Z",
                "source_job_id": None,
                "source_model_id": None,
                "raw_payload": None,
                "created_at": now,
                "updated_at": now,
            },
        ]
        self._data = {"next_id": 3, "tickets": samples}
        self._persist()

    def _generate_action_id(self) -> str:
        return f"ACT-{uuid4().hex[:8].upper()}"

    def list_tickets(self) -> list[Ticket]:
        with self._lock:
            tickets = [Ticket(**ticket) for ticket in self._data["tickets"]]
        tickets.sort(key=lambda t: t.created_at, reverse=True)
        return tickets

    def get_ticket(self, ticket_id: int) -> Ticket:
        with self._lock:
            for ticket in self._data["tickets"]:
                if ticket["id"] == ticket_id:
                    return Ticket(**ticket)
        raise TicketNotFoundError(f"Ticket {ticket_id} not found")

    def create_ticket(self, ticket_in: TicketCreate) -> Ticket:
        with self._lock:
            ticket_dict = self._ticket_dict_from_create(ticket_in)
            ticket_dict["id"] = self._data["next_id"]
            self._data["next_id"] += 1
            self._data["tickets"].append(ticket_dict)
            self._persist()
            return Ticket(**ticket_dict)

    def update_ticket(self, ticket_id: int, update: TicketUpdate) -> Ticket:
        with self._lock:
            for index, stored in enumerate(self._data["tickets"]):
                if stored["id"] != ticket_id:
                    continue
                updated = self._apply_update(stored, update)
                self._data["tickets"][index] = updated
                self._persist()
                return Ticket(**updated)
        raise TicketNotFoundError(f"Ticket {ticket_id} not found")

    def _ticket_dict_from_create(self, ticket_in: TicketCreate) -> dict[str, Any]:
        now = datetime.utcnow().isoformat()
        action_items = [self._build_action_item(item) for item in ticket_in.action_items]
        return {
            "ticket_id": ticket_in.ticket_id,
            "subject": ticket_in.subject,
            "summary": ticket_in.summary,
            "claimant_name": ticket_in.claimant_name,
            "claimant_email": ticket_in.claimant_email,
            "claimant_phone": ticket_in.claimant_phone,
            "description": ticket_in.description,
            "priority": ticket_in.priority.value,
            "status": ticket_in.status.value,
            "policy_number": ticket_in.policy_number,
            "claim_type": ticket_in.claim_type,
            "claim_date": ticket_in.claim_date,
            "incident_date": ticket_in.incident_date,
            "incident_location": ticket_in.incident_location,
            "claim_amount": ticket_in.claim_amount,
            "missing_fields": ticket_in.missing_fields,
            "has_missing_critical_fields": ticket_in.has_missing_critical_fields,
            "action_items": action_items,
            "next_steps": ticket_in.next_steps,
            "created_timestamp": ticket_in.created_timestamp,
            "source_job_id": ticket_in.source_job_id,
            "source_model_id": ticket_in.source_model_id,
            "raw_payload": ticket_in.raw_payload,
            "created_at": now,
            "updated_at": now,
        }

    def _build_action_item(self, payload: ActionItemCreate) -> dict[str, Any]:
        identifier = payload.id or self._generate_action_id()
        return {
            "id": identifier,
            "title": payload.title,
            "details": payload.details,
            "suggested_by": payload.suggested_by,
            "status": payload.status or "open",
        }

    def _apply_update(self, stored: dict[str, Any], update: TicketUpdate) -> dict[str, Any]:
        ticket = Ticket(**stored)
        data = ticket.model_dump()
        for field in (
            "ticket_id",
            "subject",
            "summary",
            "claimant_name",
            "claimant_email",
            "claimant_phone",
            "description",
            "priority",
            "status",
            "policy_number",
            "claim_type",
            "claim_date",
            "incident_date",
            "incident_location",
            "claim_amount",
            "missing_fields",
            "next_steps",
            "created_timestamp",
        ):
            value = getattr(update, field)
            if value is not None:
                if field in {"priority", "status"} and hasattr(value, "value"):
                    data[field] = value.value
                else:
                    data[field] = value
        if update.action_items is not None:
            data["action_items"] = [self._build_action_item(item) for item in update.action_items]
        data["updated_at"] = datetime.utcnow().isoformat()
        return data


store = TicketStore()


__all__ = ["TicketStore", "TicketNotFoundError", "store"]
