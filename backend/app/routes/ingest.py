from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from ..config import settings
from ..db import JobStatus, get_session
from ..db import crud as job_crud
from ..llm.registry import get_model

router = APIRouter(prefix="/ingest", tags=["ingest"])


class IngestRequest(BaseModel):
    text: str
    model_id: str | None = None


class IngestResponse(BaseModel):
    job_id: int
    model_id: str
    model_display_name: str
    status: JobStatus
    created_at: datetime


@router.post("/", response_model=IngestResponse, summary="Submit free text payload")
async def ingest_payload(payload: IngestRequest) -> IngestResponse:
    model_id = payload.model_id or settings.llm_default_model
    try:
        model = get_model(model_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    with get_session() as session:
        job = job_crud.create_job(
            session,
            text=payload.text,
            model_id=model.model_id,
            model_display_name=model.display_name,
        )

    return IngestResponse(
        job_id=job.id,
        model_id=job.model_id,
        model_display_name=job.model_display_name,
        status=job.status,
        created_at=job.created_at,
    )
