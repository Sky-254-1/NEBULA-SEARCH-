#!/bin/bash
set -euo pipefail

export PYTHONPATH=/app
APP_ENV="${APP_ENV:-production}"
LOG_LEVEL="${LOG_LEVEL:-info}"

echo "Starting Nebula Scheduler (env=${APP_ENV})..."

if echo "${DATABASE_URL:-}" | grep -q "postgresql"; then
    echo "Scheduler waiting for PostgreSQL..."
    for i in $(seq 1 30); do
        if python -c "
import asyncio, asyncpg, os
async def chk():
    await asyncpg.connect(os.environ['DATABASE_URL'])
asyncio.run(chk())
" 2>/dev/null; then
            echo "PostgreSQL is ready for scheduler"
            break
        fi
        sleep 1
    done
fi

if [ -n "${REDIS_URL:-}" ]; then
    echo "Scheduler waiting for Redis..."
    for i in $(seq 1 20); do
        if python -c "
import redis, os
redis.from_url(os.environ['REDIS_URL']).ping()
" 2>/dev/null; then
            echo "Redis is ready for scheduler"
            break
        fi
        sleep 1
    done
fi

if [ $# -gt 0 ]; then
    echo "Scheduler running custom command: $*"
    exec env PYTHONPATH=/app "$@"
fi

exec python - <<'PYEOF'
import asyncio
import logging
import signal
import sys

logging.basicConfig(
    level=getattr(logging, "${LOG_LEVEL}".upper(), logging.INFO),
    format="%(asctime)s %(levelname)s [scheduler] %(message)s"
)
logger = logging.getLogger("scheduler")

async def run():
    try:
        from app.crawler.scheduler import crawl_scheduler
        from app.indexing.scheduler import indexing_scheduler
        from app.incremental.scheduler import incremental_scheduler
        from app.services.cache import cache_service
        from app.services.queue import job_queue

        await cache_service.connect()
        await job_queue.connect()
        await crawl_scheduler.start()
        logger.info("Crawl scheduler started")

        try:
            await indexing_scheduler.start()
            logger.info("Indexing scheduler started")
        except Exception as e:
            logger.warning(f"Indexing scheduler start failed: {e}")

        try:
            await incremental_scheduler.start()
            logger.info("Incremental reindex scheduler started")
        except Exception as e:
            logger.warning(f"Incremental scheduler start failed: {e}")

        logger.info("Nebula Scheduler running — all systems go")

        stop = asyncio.Event()
        for sig in (signal.SIGTERM, signal.SIGINT):
            try:
                loop = asyncio.get_running_loop()
                loop.add_signal_handler(sig, stop.set)
            except NotImplementedError:
                pass

        await stop.wait()

        logger.info("Shutdown signal received — stopping schedulers")
        try:
            await crawl_scheduler.stop()
        except Exception:
            pass
        try:
            await indexing_scheduler.stop()
        except Exception:
            pass
        await cache_service.close()
        await job_queue.close()
        logger.info("Scheduler shut down cleanly")

    except Exception:
        logger.exception("Scheduler crashed")
        sys.exit(1)

asyncio.run(run())
PYEOF

