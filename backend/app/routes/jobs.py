from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from ..config import settings
from ..db import Job, JobStatus, get_session
from ..db import crud as job_crud
from ..ticketing import TargetAPIError, submit_ticket

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

        payload = job.result_json

    if settings.target_api_base_url is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Target API base URL is not configured",
        )

    try:
        target_response = await submit_ticket(payload)
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
