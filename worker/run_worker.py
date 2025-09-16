from __future__ import annotations

import asyncio
import logging
import signal
from contextlib import asynccontextmanager

from backend.app.config import settings
from backend.app.db import get_session
from backend.app.db import crud as job_crud
from backend.app.llm.registry import get_model

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
