"""Standalone worker process entrypoint for document indexing.

Run with:  python -m app.workers.indexer_entrypoint
"""

import asyncio
import logging
import signal
import sys

from app.config import get_settings
from app.database import init_db
from app.database.engine import close_pool, init_pool
from app.services.queue import job_queue
from app.workers.indexer import IndexingWorker

logger = logging.getLogger("nebula.indexer")
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
    logger.info("Starting Nebula document indexing worker")

    # Initialize database and queue
    await init_db()
    await init_pool()
    await job_queue.connect()

    # Create and start worker
    worker = IndexingWorker(max_retries=3)
    await worker.connect()
    logger.info("Worker initialized — waiting for index_document jobs")

    try:
        # Run the worker loop
        await worker.run()
    except asyncio.CancelledError:
        logger.info("Worker loop cancelled")
    finally:
        logger.info("Stopping worker …")
        await worker.close()
        await job_queue.close()
        await close_pool()
        logger.info("Worker shutdown complete")


if __name__ == "__main__":
    if sys.platform != "win32":
        import os

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, lambda s=sig: _handle_signal(s))

        try:
            loop.run_until_complete(main())
        finally:
            loop.close()
    else:
        # Windows signal handling
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            logger.info("Received KeyboardInterrupt — shutting down")
            asyncio.run(close_pool())
