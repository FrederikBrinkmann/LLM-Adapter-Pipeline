from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/ingest", tags=["ingest"])


class IngestRequest(BaseModel):
    text: str


class IngestResponse(BaseModel):
    message: str
    length: int


@router.post("/", response_model=IngestResponse, summary="Submit free text payload")
async def ingest_payload(payload: IngestRequest) -> IngestResponse:
    return IngestResponse(message="Payload received", length=len(payload.text))
