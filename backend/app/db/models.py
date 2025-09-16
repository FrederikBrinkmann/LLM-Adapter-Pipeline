from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import JSON, Column, Text
from sqlmodel import Field, SQLModel


class JobStatus(str, Enum):
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class Job(SQLModel, table=True):
    __tablename__ = "jobs"

    id: Optional[int] = Field(default=None, primary_key=True)
    input_text: str = Field(sa_column=Column(Text, nullable=False))
    model_id: str = Field(index=True)
    model_display_name: str = Field(nullable=False)
    status: JobStatus = Field(default=JobStatus.QUEUED, index=True)
    result_json: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    submitted_at: Optional[datetime] = None
    target_status: Optional[str] = None
    target_reference: Optional[str] = None
    target_response: Optional[dict] = Field(default=None, sa_column=Column(JSON))


class JobRead(SQLModel):
    id: int
    model_id: str
    model_display_name: str
    status: JobStatus
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    submitted_at: Optional[datetime]
    target_status: Optional[str]
    target_reference: Optional[str]
    error_message: Optional[str]
    result_json: Optional[dict]


__all__ = ["Job", "JobRead", "JobStatus"]
