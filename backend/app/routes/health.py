from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/", summary="Health status")
def health_status() -> dict[str, str]:
    return {"status": "ok"}
