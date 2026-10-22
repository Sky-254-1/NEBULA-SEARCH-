"""Standalone worker process entrypoint.

Run with:  python -m app.indexing.worker_entrypoint
"""

import asyncio
import logging
import signal

from app.config import get_settings
from app.database import init_db
from app.database.engine import close_pool, init_pool
from app.indexing.worker import get_worker_pool
from app.services.cache import cache_service
from app.services.queue import job_queue

logger = logging.getLogger("nebula.worker")
settings = get_settings()

_shutdown_event = asyncio.Event()


def _handle_signal(sig):
    logger.info("Received signal %s — initiating shutdown", sig)
    _shutdown_event.set()


async def main() -> None:
    logging.basicConfig(
        level=settings.log_level.upper(),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    logger.info("Starting Nebula indexing worker")

    await init_db()
    await init_pool()
    await cache_service.connect()
    await job_queue.connect()

    pool = get_worker_pool()
    await pool.start()
    logger.info("Worker pool started — waiting for jobs")

    try:
        await _shutdown_event.wait()
    finally:
        logger.info("Stopping worker pool …")
        await pool.stop()
        await job_queue.close()
        await cache_service.close()
        await close_pool()
        logger.info("Worker shutdown complete")


if __name__ == "__main__":
    import os

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    if os.name != "nt":
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, lambda s=sig: _handle_signal(s))

    try:
        loop.run_until_complete(main())
    finally:
        loop.close()
