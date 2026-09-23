"""Background worker for incremental document indexing."""

import asyncio
import logging
import sys
from pathlib import Path

# Ensure backend root is on path when run as script
_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from app.config import get_settings
from app.database import init_db
from app.database.engine import connect
from app.services.queue import job_queue
from vector.pipeline import index_document

logger = logging.getLogger("nebula.vector.worker")
POLL_INTERVAL = 2.0


async def process_job(job: dict) -> None:
    job_type = job.get("type")
    payload = job.get("payload", {})
    if job_type != "index_document":
        logger.debug("Skipping unknown job type: %s", job_type)
        return

    document_id = payload.get("document_id")
    user_id = payload.get("user_id")
    if not document_id or not user_id:
        return

    db = await connect()
    try:
        await index_document(db, document_id, user_id)
    finally:
        await db.close()


async def run_worker(poll_interval: float = POLL_INTERVAL) -> None:
    get_settings.cache_clear()
    await init_db()
    await job_queue.connect()
    logger.info("Vector indexing worker started")
    while True:
        job = await job_queue.dequeue()
        if job:
            try:
                await process_job(job)
            except Exception:
                logger.exception("Worker job failed")
        else:
            await asyncio.sleep(poll_interval)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_worker())


if __name__ == "__main__":
    main()
