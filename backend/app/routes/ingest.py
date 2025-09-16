from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from ..config import settings
from ..llm.registry import get_model

router = APIRouter(prefix="/ingest", tags=["ingest"])


class IngestRequest(BaseModel):
    text: str
    model_id: str | None = None


class IngestResponse(BaseModel):
    model_id: str
    model_display_name: str
    result: dict[str, Any]


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

    result = await model.generate_structured(text=payload.text)
    return IngestResponse(
        model_id=model.model_id,
        model_display_name=model.display_name,
        result=result,
    )
