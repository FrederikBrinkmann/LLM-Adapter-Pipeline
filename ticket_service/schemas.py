from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class TicketStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    WAITING_FOR_CUSTOMER = "waiting_for_customer"
    DONE = "done"


class TicketPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class ActionItemBase(BaseModel):
    title: str = Field(..., min_length=1)
    details: str | None = None
    suggested_by: Literal["llm", "agent", "system"] = "llm"


class ActionItem(ActionItemBase):
    id: str
    status: Literal["open", "done"] = "open"


class ActionItemCreate(ActionItemBase):
    id: str | None = None
    status: Literal["open", "done"] | None = None


class Ticket(BaseModel):
    id: int
    subject: str
    summary: str
    customer: str | None = None
    description: str | None = None
    priority: TicketPriority
    status: TicketStatus
    order_number: str | None = None
    claim_type: str | None = None
    missing_fields: list[str] = Field(default_factory=list)
    action_items: list[ActionItem] = Field(default_factory=list)
    source_job_id: int | None = None
    source_model_id: str | None = None
    raw_payload: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime


class TicketCreate(BaseModel):
    summary: str = Field(..., min_length=1)
    subject: str | None = None
    customer: str | None = None
    description: str | None = None
    priority: TicketPriority = TicketPriority.MEDIUM
    status: TicketStatus = TicketStatus.TODO
    order_number: str | None = None
    claim_type: str | None = None
    missing_fields: list[str] = Field(default_factory=list)
    action_items: list[ActionItemCreate] = Field(default_factory=list)
    source_job_id: int | None = None
    source_model_id: str | None = None
    raw_payload: dict[str, Any] | None = None

    @model_validator(mode="after")
    def ensure_subject(self) -> "TicketCreate":
        subject = self.subject or self.summary
        subject = subject.strip() if subject else "Ticket"
        if len(subject) > 120:
            subject = f"{subject[:117]}..."
        self.subject = subject
        return self


class TicketUpdate(BaseModel):
    subject: str | None = None
    summary: str | None = None
    customer: str | None = None
    description: str | None = None
    priority: TicketPriority | None = None
    status: TicketStatus | None = None
    order_number: str | None = None
    claim_type: str | None = None
    missing_fields: list[str] | None = None
    action_items: list[ActionItemCreate] | None = None

    @model_validator(mode="after")
    def normalize_subject(self) -> "TicketUpdate":
        if self.subject:
            subject = self.subject.strip()
            if len(subject) > 120:
                subject = f"{subject[:117]}..."
            self.subject = subject
        return self


__all__ = [
    "ActionItem",
    "ActionItemCreate",
    "Ticket",
    "TicketCreate",
    "TicketPriority",
    "TicketStatus",
    "TicketUpdate",
]
