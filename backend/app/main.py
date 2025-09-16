from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .llm.setup import initialize_models
from .routes import health, ingest, models

app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    version=settings.api_version,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.backend_cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event() -> None:
    initialize_models()


@app.get("/", summary="Service info")
def read_root() -> dict[str, str]:
    return {"message": "LLM Adapter Pipeline API is running."}


app.include_router(health.router)
app.include_router(ingest.router)
app.include_router(models.router)
