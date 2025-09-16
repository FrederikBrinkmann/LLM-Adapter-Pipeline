from fastapi import APIRouter
from pydantic import BaseModel

from ..config import settings
from ..llm.registry import list_models

router = APIRouter(prefix="/models", tags=["models"])


class ModelInfo(BaseModel):
    model_id: str
    display_name: str
    supports_streaming: bool
    is_default: bool


@router.get("/", response_model=list[ModelInfo], summary="List available LLM models")
async def get_models() -> list[ModelInfo]:
    models = list_models()
    default_id = settings.llm_default_model
    return [
        ModelInfo(
            model_id=model.model_id,
            display_name=model.display_name,
            supports_streaming=bool(getattr(model, "supports_streaming", False)),
            is_default=model.model_id == default_id,
        )
        for model in models
    ]
