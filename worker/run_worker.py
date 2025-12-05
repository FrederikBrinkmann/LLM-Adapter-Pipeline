from __future__ import annotations

import asyncio
import logging
import signal
import sys
from pathlib import Path

import httpx

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.app.config import settings
from backend.app.db import get_session, init_db
from backend.app.db import crud as job_crud
from backend.app.llm.registry import get_model
from backend.app.llm.setup import initialize_models

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


async def process_job(job) -> None:
    job_id = job.id
    logger.info("Processing job %s with model %s", job_id, job.model_id)
    try:
        model = get_model(job.model_id)
    except KeyError as exc:
        logger.error("Model %s not found for job %s", job.model_id, job_id)
        with get_session() as session:
            job_crud.mark_job_failed(session, job_id, str(exc))
        return

    try:
        result = await model.generate_structured(text=job.input_text)
    except Exception as exc:  # noqa: BLE001
        logger.exception("LLM processing failed for job %s", job_id)
        with get_session() as session:
            job_crud.mark_job_failed(session, job_id, str(exc))
        return

    with get_session() as session:
        job_crud.mark_job_completed(session, job_id, result=result)
    logger.info("Job %s completed", job_id)

    await maybe_auto_submit(job_id, result)


async def maybe_auto_submit(job_id: int, result: dict) -> None:
    if not settings.auto_submit_enabled:
        return
    if settings.target_api_base_url is None:
        logger.info("Skipping auto-submit for job %s: target API not configured", job_id)
        return

    missing = result.get("missing_fields") or []
    if missing and not settings.auto_submit_allow_missing_fields:
        logger.info("Skipping auto-submit for job %s: missing_fields present", job_id)
        return

    api_base = settings.auto_submit_api_base.rstrip("/")
    url = f"{api_base}/jobs/{job_id}/submit"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(url)
            response.raise_for_status()
        logger.info("Auto-submit for job %s succeeded (status %s)", job_id, response.status_code)
    except Exception:  # noqa: BLE001
        logger.exception("Auto-submit for job %s failed", job_id)


async def worker_loop() -> None:
    logger.info("Worker started. Poll interval %.2fs", settings.worker_poll_interval)
    while True:
        with get_session() as session:
            job = job_crud.acquire_next_job(session)

        if job is None:
            await asyncio.sleep(settings.worker_poll_interval)
            continue

        await process_job(job)
        await asyncio.sleep(0)


def main() -> None:
    logger.info("Initializing database and model registry")
    init_db()
    initialize_models()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    stop_event = asyncio.Event()

    def _signal_handler(*_: int) -> None:
        logger.info("Stopping worker ...")
        stop_event.set()

    loop.add_signal_handler(signal.SIGINT, _signal_handler)
    loop.add_signal_handler(signal.SIGTERM, _signal_handler)

    async def _run() -> None:
        worker_task = asyncio.create_task(worker_loop())
        await stop_event.wait()
        worker_task.cancel()
        try:
            await worker_task
        except asyncio.CancelledError:
            logger.info("Worker stopped")

    loop.run_until_complete(_run())


if __name__ == "__main__":
    main()
