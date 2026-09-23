"""Crawl job scheduler with priority queue, status tracking, and recurring jobs."""

import asyncio
import logging
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Callable, Coroutine

import httpx

from app.config import get_settings
from app.crawler.crawler import AsyncCrawler

logger = logging.getLogger("nebula.crawler.scheduler")
settings = get_settings()


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"
    SCHEDULED = "scheduled"


@dataclass
class CrawlJob:
    id: str
    url: str
    status: JobStatus = JobStatus.PENDING
    max_pages: int = 10
    depth: int = 3
    priority: int = 0
    pages_crawled: int = 0
    error_message: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    schedule_interval: int | None = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "url": self.url,
            "status": self.status.value,
            "max_pages": self.max_pages,
            "depth": self.depth,
            "priority": self.priority,
            "pages_crawled": self.pages_crawled,
            "error_message": self.error_message,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "created_at": self.created_at,
            "schedule_interval": self.schedule_interval,
        }


JobCallback = Callable[[CrawlJob], Coroutine[None, None, None]]


class CrawlJobScheduler:
    """In-memory job scheduler with priority queue and recurring job support."""

    def __init__(self):
        self._jobs: dict[str, CrawlJob] = {}
        self._queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._running = False
        self._worker_task: asyncio.Task | None = None
        self._scheduler_task: asyncio.Task | None = None
        self._crawler = AsyncCrawler()
        self._callbacks: dict[str, list[JobCallback]] = defaultdict(list)
        self._pending_urls: dict[str, list[str]] = defaultdict(list)
        self._stop_events: dict[str, asyncio.Event] = {}

    @property
    def crawler(self) -> AsyncCrawler:
        return self._crawler

    def on(self, event: str, callback: JobCallback):
        self._callbacks[event].append(callback)

    async def _emit(self, event: str, job: CrawlJob):
        for cb in self._callbacks.get(event, []):
            try:
                await cb(job)
            except Exception as exc:
                logger.error("Callback error for event %s: %s", event, exc)

    async def create_job(
        self,
        url: str,
        max_pages: int = 10,
        depth: int = 3,
        priority: int = 0,
        schedule_interval: int | None = None,
    ) -> str:
        job_id = str(uuid.uuid4())
        job = CrawlJob(
            id=job_id,
            url=url,
            max_pages=max_pages,
            depth=depth,
            priority=priority,
            schedule_interval=schedule_interval,
            status=JobStatus.SCHEDULED if schedule_interval else JobStatus.PENDING,
        )
        self._jobs[job_id] = job
        await self._queue.put((priority, time.time(), job_id))
        logger.info("Created crawl job %s for %s", job_id, url)
        await self._emit("created", job)
        return job_id

    async def stop_job(self, job_id: str) -> bool:
        job = self._jobs.get(job_id)
        if not job:
            return False
        if job.status in (JobStatus.COMPLETED, JobStatus.STOPPED, JobStatus.FAILED):
            return False
        job.status = JobStatus.STOPPED
        job.completed_at = datetime.now(timezone.utc).isoformat()
        if job_id in self._stop_events:
            self._stop_events[job_id].set()
        await self._emit("stopped", job)
        return True

    def get_job(self, job_id: str) -> CrawlJob | None:
        return self._jobs.get(job_id)

    def list_jobs(self, status: str | None = None) -> list[CrawlJob]:
        jobs = list(self._jobs.values())
        if status:
            jobs = [j for j in jobs if j.status.value == status]
        return sorted(jobs, key=lambda j: j.created_at, reverse=True)

    async def _execute_job(self, job: CrawlJob):
        logger.info("Starting crawl job %s for %s", job.id, job.url)
        job.status = JobStatus.RUNNING
        job.started_at = datetime.now(timezone.utc).isoformat()
        await self._emit("started", job)

        stop_event = asyncio.Event()
        self._stop_events[job.id] = stop_event

        client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            limits=httpx.Limits(max_keepalive_connections=settings.crawler_max_concurrency),
        )

        try:
            queue: list[tuple[str, int]] = [(job.url, 0)]
            seen_urls: set[str] = set()

            async def on_crawled(data: dict):
                if stop_event.is_set():
                    return
                job.pages_crawled += 1

            self._crawler.on_content_extracted(on_crawled)

            async with client:
                while queue and job.pages_crawled < job.max_pages and not stop_event.is_set():
                    url, depth = queue.pop(0)
                    if url in seen_urls:
                        continue
                    seen_urls.add(url)

                    discovered = await self._crawler.crawl_page(url, depth, client)
                    if stop_event.is_set():
                        break
                    for link in discovered:
                        if len(queue) + job.pages_crawled < job.max_pages:
                            queue.append((link, depth + 1))

            self._crawler._content_callbacks.remove(on_crawled)

            if stop_event.is_set():
                job.status = JobStatus.STOPPED
            else:
                job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now(timezone.utc).isoformat()
            logger.info("Job %s completed: %d pages crawled", job.id, job.pages_crawled)
            await self._emit("completed", job)

        except Exception as exc:
            job.status = JobStatus.FAILED
            job.error_message = str(exc)
            job.completed_at = datetime.now(timezone.utc).isoformat()
            logger.exception("Job %s failed: %s", job.id, exc)
            await self._emit("failed", job)
        finally:
            self._stop_events.pop(job.id, None)

    async def _worker_loop(self):
        while self._running:
            try:
                _, _, job_id = await asyncio.wait_for(self._queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue

            job = self._jobs.get(job_id)
            if not job:
                continue
            if job.status in (JobStatus.STOPPED, JobStatus.FAILED):
                continue

            await self._execute_job(job)

            if job.schedule_interval and job.status == JobStatus.COMPLETED:
                await asyncio.sleep(job.schedule_interval)
                if self._running and job.status != JobStatus.STOPPED:
                    new_id = await self.create_job(
                        job.url,
                        max_pages=job.max_pages,
                        depth=job.depth,
                        priority=job.priority,
                        schedule_interval=job.schedule_interval,
                    )
                    logger.info("Rescheduled job %s as %s", job.id, new_id)

    async def _schedule_loop(self):
        while self._running:
            try:
                now = time.time()
                for job in list(self._jobs.values()):
                    if job.schedule_interval is None:
                        continue
                    if job.status in (JobStatus.RUNNING, JobStatus.PENDING, JobStatus.STOPPED, JobStatus.FAILED):
                        continue
                    last_run = 0.0
                    if job.completed_at:
                        try:
                            dt = datetime.fromisoformat(job.completed_at.replace("Z", "+00:00"))
                            last_run = dt.timestamp()
                        except (ValueError, TypeError):
                            pass
                    if job.started_at and not job.completed_at:
                        try:
                            dt = datetime.fromisoformat(job.started_at.replace("Z", "+00:00"))
                            last_run = dt.timestamp()
                        except (ValueError, TypeError):
                            pass
                    if now - last_run >= job.schedule_interval:
                        job.status = JobStatus.PENDING
                        await self._queue.put((job.priority, time.time(), job.id))
                        logger.info("Re-queued scheduled job %s for %s", job.id, job.url)
            except Exception as exc:
                logger.exception("Schedule loop error: %s", exc)
            await asyncio.sleep(30)

    async def start(self):
        if self._running:
            return
        self._running = True
        self._worker_task = asyncio.create_task(self._worker_loop())
        self._scheduler_task = asyncio.create_task(self._schedule_loop())
        logger.info("Crawl job scheduler started")

    async def stop(self):
        self._running = False
        for job_id in list(self._jobs.keys()):
            await self.stop_job(job_id)
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
        logger.info("Crawl job scheduler stopped")


_scheduler: CrawlJobScheduler | None = None


def get_scheduler() -> CrawlJobScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = CrawlJobScheduler()
    return _scheduler


crawl_scheduler = get_scheduler()
