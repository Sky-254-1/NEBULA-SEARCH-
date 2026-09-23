"""Robots.txt parser with caching and crawl-delay support."""

import logging
import time
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx

from app.config import get_settings

logger = logging.getLogger("nebula.crawler.robots")
settings = get_settings()


class RobotsParser:
    """Caching robots.txt parser that respects crawl-delay."""

    def __init__(self, user_agent: str | None = None, cache_ttl: int | None = None):
        self._user_agent = user_agent or settings.crawler_user_agent
        self._cache_ttl = cache_ttl or settings.crawler_robots_ttl
        self._cache: dict[str, tuple[float, RobotFileParser]] = {}
        self._delay_cache: dict[str, float] = {}

    async def _fetch_robots(self, netloc: str, scheme: str) -> RobotFileParser | None:
        robots_url = f"{scheme}://{netloc}/robots.txt"
        rp = RobotFileParser()
        try:
            async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
                resp = await client.get(robots_url, headers={"User-Agent": self._user_agent})
                if resp.status_code == 200:
                    rp.parse(resp.text.splitlines())
                else:
                    rp.allow_all = True
        except Exception as exc:
            logger.debug("Failed to fetch robots.txt from %s: %s", robots_url, exc)
            rp.allow_all = True
        self._cache[netloc] = (time.time(), rp)
        return rp

    async def can_fetch(self, url: str) -> bool:
        parsed = urlparse(url)
        netloc = parsed.netloc.lower()
        scheme = parsed.scheme.lower()
        now = time.time()

        if netloc in self._cache:
            cached_at, rp = self._cache[netloc]
            if now - cached_at < self._cache_ttl:
                return rp.can_fetch(self._user_agent, url)

        rp = await self._fetch_robots(netloc, scheme)
        return rp.can_fetch(self._user_agent, url)

    async def get_crawl_delay(self, url: str) -> float:
        parsed = urlparse(url)
        netloc = parsed.netloc.lower()
        scheme = parsed.scheme.lower()

        if netloc not in self._cache:
            await self._fetch_robots(netloc, scheme)

        if netloc in self._cache:
            _, rp = self._cache[netloc]
            delay = rp.crawl_delay(self._user_agent)
            if delay is not None:
                return float(delay)
        return settings.crawler_default_delay

    def get_domain(self, url: str) -> str:
        return urlparse(url).netloc.lower()
