"""Standalone scheduler process entrypoint.

Run with:  python -m app.indexing.scheduler_entrypoint
"""

import asyncio
import logging
import signal

from app.config import get_settings
from app.database import init_db
from app.database.engine import close_pool, init_pool
from app.indexing.scheduler import get_scheduler, ScheduleType
from app.services.cache import cache_service
from app.services.queue import job_queue

logger = logging.getLogger("nebula.scheduler")
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
    logger.info("Starting Nebula indexing scheduler")

    await init_db()
    await init_pool()
    await cache_service.connect()
    await job_queue.connect()

    scheduler = get_scheduler()

    # Register the three main scheduled tasks
    scheduler.register_task(
        name="nightly_reindex",
        schedule_type=ScheduleType.INTERVAL,
        interval_seconds=86400,  # 24 h
        callback=scheduler.trigger_nightly_reindex,
    )
    scheduler.register_task(
        name="weekly_optimization",
        schedule_type=ScheduleType.INTERVAL,
        interval_seconds=604800,  # 7 days
        callback=scheduler.trigger_weekly_optimization,
    )
    scheduler.register_task(
        name="scan_missing",
        schedule_type=ScheduleType.INTERVAL,
        interval_seconds=3600,  # 1 h
        callback=scheduler.scan_missing_documents,
    )

    await scheduler.start()
    logger.info("Scheduler started with %d tasks", len(scheduler.get_all_tasks()))

    try:
        await _shutdown_event.wait()
    finally:
        logger.info("Stopping scheduler …")
        await scheduler.stop()
        await job_queue.close()
        await cache_service.close()
        await close_pool()
        logger.info("Scheduler shutdown complete")


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
