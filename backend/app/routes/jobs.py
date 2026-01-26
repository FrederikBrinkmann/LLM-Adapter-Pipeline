from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from ..config import settings
from ..db import Job, JobStatus, get_session
from ..db import crud as job_crud
from ..ticketing import TargetAPIError, submit_ticket

ACTION_SOURCES = {"llm", "agent", "system"}


def _derive_priority(
    claim_type: str | None,
    claim_amount: float | None,
    missing_fields: list[str],
) -> str:
    if isinstance(claim_amount, (int, float)):
        if claim_amount >= 50000:
            return "urgent"
        if claim_amount >= 10000:
            return "high"
    if claim_type:
        claim = claim_type.lower()
        if claim in {"death", "medical"}:
            return "urgent"
        if claim in {"liability", "damage"}:
            return "high"
    if len(missing_fields) >= 4:
        return "high"
    return "medium"


def _prepare_ticket_payload(job: Job, structured_payload: dict[str, Any]) -> dict[str, Any]:
    summary = str(structured_payload.get("summary") or "").strip() or job.input_text.strip()
    if not summary:
        summary = f"Ticket für Job #{job.id}"
    subject = str(structured_payload.get("subject") or summary).strip()
    priority_raw = structured_payload.get("priority")
    valid_priorities = {"low", "medium", "high", "urgent"}
    priority: str | None = None
    if isinstance(priority_raw, str) and priority_raw.lower() in valid_priorities:
        priority = priority_raw.lower()

    missing_fields: list[str] = []
    raw_missing = structured_payload.get("missing_fields") or []
    if isinstance(raw_missing, list):
        for entry in raw_missing:
            if isinstance(entry, str):
                cleaned = entry.strip()
                if cleaned and cleaned.lower() not in {"model_id"}:
                    missing_fields.append(cleaned)

    raw_actions = structured_payload.get("action_items") or []
    action_items: list[dict[str, Any]] = []
    if isinstance(raw_actions, list):
        # Normalize both string and object formats to uniform structure
        # Supports hybrid: LLM can return ["string"] or [{"title": "...", "details": "..."}]
        for entry in raw_actions:
            if isinstance(entry, str):
                text = entry.strip()
                if not text:
                    continue
                action_items.append(
                    {
                        "title": text[:80],
                        "details": text,
                        "suggested_by": "llm",
                    }
                )
            elif isinstance(entry, dict):
                title = str(entry.get("title") or entry.get("label") or "").strip()
                if not title:
                    continue
                details_value = entry.get("details") or entry.get("description") or entry.get("text") or title
                suggested_by = str(entry.get("suggested_by") or "llm").lower()
                action_items.append(
                    {
                        "title": title[:80],
                        "details": str(details_value),
                        "suggested_by": suggested_by if suggested_by in ACTION_SOURCES else "llm",
                        "status": entry.get("status") if entry.get("status") in {"open", "done"} else "open",
                    }
                )

    claim_type = structured_payload.get("claim_type")
    claim_amount_raw = structured_payload.get("claim_amount")
    claim_amount: float | None = None
    if isinstance(claim_amount_raw, (int, float)):
        claim_amount = float(claim_amount_raw)
    elif isinstance(claim_amount_raw, str):
        try:
            claim_amount = float(claim_amount_raw.replace(",", "."))
        except ValueError:
            claim_amount = None

    if priority is None:
        priority = _derive_priority(claim_type, claim_amount, missing_fields)

    claimant_name = structured_payload.get("claimant_name")
    policy_number = structured_payload.get("policy_number")

    # Markiere wenn kritische Felder fehlen (3+)
    critical_fields = {"claimant_name", "policy_number", "claim_date", "incident_date", "claim_type"}
    missing_critical_count = 0
    for field in critical_fields:
        value = structured_payload.get(field) if field in critical_fields else None
        if not value or (isinstance(value, str) and not value.strip()):
            missing_critical_count += 1
    has_missing_critical = missing_critical_count >= 3

    return {
        "subject": subject or summary,
        "summary": summary,
        "ticket_id": structured_payload.get("ticket_id"),
        "claimant_name": claimant_name,
        "claimant_email": structured_payload.get("claimant_email"),
        "claimant_phone": structured_payload.get("claimant_phone"),
        "description": structured_payload.get("description") or job.input_text,
        "priority": priority,
        "status": "todo",
        "policy_number": policy_number,
        "claim_type": claim_type,
        "claim_date": structured_payload.get("claim_date"),
        "incident_date": structured_payload.get("incident_date"),
        "incident_location": structured_payload.get("incident_location"),
        "claim_amount": claim_amount,
        "missing_fields": missing_fields,
        "has_missing_critical_fields": has_missing_critical,
        "action_items": action_items,
        "next_steps": structured_payload.get("next_steps"),
        "created_timestamp": structured_payload.get("created_timestamp"),
        "source_job_id": job.id,
        "source_model_id": job.model_id,
        "raw_payload": structured_payload,
    }

router = APIRouter(prefix="/jobs", tags=["jobs"])


class JobSummary(BaseModel):
    id: int
    model_id: str
    model_display_name: str
    status: JobStatus
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    submitted_at: Optional[datetime]


class JobDetail(JobSummary):
    result_json: Optional[dict]
    error_message: Optional[str]
    target_status: Optional[str]
    target_reference: Optional[str]


class JobSubmitResponse(BaseModel):
    job: JobDetail
    target_response: Optional[dict]


def _serialize_job(job: Job) -> JobDetail:
    return JobDetail(
        id=job.id,
        model_id=job.model_id,
        model_display_name=job.model_display_name,
        status=job.status,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        submitted_at=job.submitted_at,
        result_json=job.result_json,
        error_message=job.error_message,
        target_status=job.target_status,
        target_reference=job.target_reference,
    )


@router.get("/", response_model=list[JobSummary], summary="List latest jobs")
async def list_jobs(limit: int = 25) -> list[JobSummary]:
    with get_session() as session:
        jobs = job_crud.list_jobs(session, limit=limit)
        return [
            JobSummary(
                id=job.id,
                model_id=job.model_id,
                model_display_name=job.model_display_name,
                status=job.status,
                created_at=job.created_at,
                started_at=job.started_at,
                completed_at=job.completed_at,
                submitted_at=job.submitted_at,
            )
            for job in jobs
        ]


@router.get("/{job_id}", response_model=JobDetail, summary="Fetch job details")
async def get_job(job_id: int) -> JobDetail:
    with get_session() as session:
        job = job_crud.get_job(session, job_id)
        if job is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
        return _serialize_job(job)


@router.post(
    "/{job_id}/submit",
    response_model=JobSubmitResponse,
    summary="Submit completed job to the target ticket system",
)
async def submit_job(job_id: int) -> JobSubmitResponse:
    with get_session() as session:
        job = job_crud.get_job(session, job_id)
        if job is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
        if job.status != JobStatus.COMPLETED or job.result_json is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Job is not completed yet or missing result",
            )

        structured_payload = job.result_json

    if settings.target_api_base_url is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Target API base URL is not configured",
        )

    try:
        ticket_payload = _prepare_ticket_payload(job, structured_payload)
        target_response = await submit_ticket(ticket_payload)
    except TargetAPIError as exc:
        with get_session() as session:
            job_crud.mark_job_submitted(
                session,
                job_id,
                status="failed",
                response_payload={"error": str(exc)},
            )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    reference = None
    if isinstance(target_response, dict):
        reference = str(target_response.get("id") or target_response.get("ticket_id") or "") or None

    with get_session() as session:
        job = job_crud.mark_job_submitted(
            session,
            job_id,
            status="submitted",
            reference=reference,
            response_payload=target_response if isinstance(target_response, dict) else None,
        )

    return JobSubmitResponse(job=_serialize_job(job), target_response=target_response)
