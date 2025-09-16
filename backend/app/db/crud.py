from __future__ import annotations

from datetime import datetime
from typing import Iterable, Optional

from sqlmodel import Session, select

from .models import Job, JobStatus


def create_job(
    session: Session,
    *,
    text: str,
    model_id: str,
    model_display_name: str,
) -> Job:
    job = Job(
        input_text=text,
        model_id=model_id,
        model_display_name=model_display_name,
        status=JobStatus.QUEUED,
    )
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def get_job(session: Session, job_id: int) -> Optional[Job]:
    return session.get(Job, job_id)


def list_jobs(session: Session, limit: int = 50) -> Iterable[Job]:
    statement = select(Job).order_by(Job.created_at.desc()).limit(limit)
    return session.exec(statement).all()


def acquire_next_job(session: Session) -> Optional[Job]:
    statement = (
        select(Job)
        .where(Job.status == JobStatus.QUEUED)
        .order_by(Job.created_at)
        .limit(1)
    )
    job = session.exec(statement).one_or_none()
    if job is None:
        return None

    job.status = JobStatus.IN_PROGRESS
    job.started_at = datetime.utcnow()
    job.updated_at = datetime.utcnow()
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def mark_job_completed(session: Session, job_id: int, result: dict) -> Job:
    job = session.get(Job, job_id)
    if job is None:
        raise ValueError(f"Job {job_id} not found")
    job.result_json = result
    job.status = JobStatus.COMPLETED
    job.completed_at = datetime.utcnow()
    job.updated_at = datetime.utcnow()
    job.error_message = None
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def mark_job_failed(session: Session, job_id: int, error_message: str) -> Job:
    job = session.get(Job, job_id)
    if job is None:
        raise ValueError(f"Job {job_id} not found")
    job.status = JobStatus.FAILED
    job.error_message = error_message
    job.completed_at = datetime.utcnow()
    job.updated_at = datetime.utcnow()
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def mark_job_submitted(
    session: Session,
    job_id: int,
    *,
    status: str,
    reference: str | None = None,
    response_payload: dict | None = None,
) -> Job:
    job = session.get(Job, job_id)
    if job is None:
        raise ValueError(f"Job {job_id} not found")
    job.submitted_at = datetime.utcnow()
    job.target_status = status
    job.target_reference = reference
    job.target_response = response_payload
    job.updated_at = datetime.utcnow()
    session.add(job)
    session.commit()
    session.refresh(job)
    return job
