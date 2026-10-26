"""Async web crawler with polite crawling, content extraction, and callback system."""

import asyncio
import logging
import re
from collections import defaultdict
from datetime import datetime, timezone
from typing import Callable, Coroutine
from urllib.parse import urljoin, urlparse, urlunparse

import httpx
from bs4 import BeautifulSoup, Tag
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.crawler.robots import RobotsParser
from app.crawler.ssrf_protection import (
    SSRFProtectionError,
    SSRFValidator,
    normalize_url,
)

logger = logging.getLogger("nebula.crawler")
settings = get_settings()

CrawlCallback = Callable[[str], Coroutine[None, None, None]]
ContentCallback = Callable[[dict], Coroutine[None, None, None]]

_URL_BLACKLIST = re.compile(
    r"\.(pdf|zip|tar|gz|bz2|rar|7z|exe|dmg|apk|iso|bin|"
    r"jpg|jpeg|png|gif|bmp|svg|webp|ico|tiff|"
    r"mp3|mp4|avi|mov|wmv|flv|mkv|webm|"
    r"css|js|json|xml|rss|atom|woff|woff2|ttf|eot)$",
    re.IGNORECASE,
)

_CONTENT_TYPES = {"text/html", "text/plain", "application/xhtml+xml"}

# Global SSRF validator instance
_ssrfer = SSRFValidator(
    max_redirects=settings.crawler_max_depth,
    allow_http_downgrade=False,
)


def _extract_links(html: str, base_url: str) -> set[str]:
    """Extract links from HTML, validating each one for SSRF."""
    soup = BeautifulSoup(html, "lxml")
    links = set()
    
    for a in soup.find_all("a", href=True):
        if not isinstance(a, Tag):
            continue
        href = a.get("href", "").strip()
        rel = a.get("rel", [])
        if isinstance(rel, str):
            rel = [rel]
        rel_lower = {r.lower() for r in rel}
        if "nofollow" in rel_lower or "none" in rel_lower:
            continue
        absolute = urljoin(base_url, href)
        # Normalize before SSRF validation
        absolute = normalize_url(absolute)
        if absolute.startswith(("http://", "https://")):
            links.add(absolute)
    
    return links


def extract_content(html: str, url: str) -> dict:
    soup = BeautifulSoup(html, "lxml")
    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()

    meta_desc = ""
    meta = soup.find("meta", attrs={"name": "description"})
    if meta and isinstance(meta, Tag) and meta.get("content"):
        meta_desc = meta.get("content", "").strip()

    for elem in soup.find_all(["script", "style", "nav", "footer", "header", "aside"]):
        elem.decompose()

    text = soup.get_text(separator=" ", strip=True)
    text = re.sub(r"\s+", " ", text).strip()

    headings = []
    for tag in ("h1", "h2", "h3"):
        for h in soup.find_all(tag):
            txt = h.get_text(strip=True)
            if txt:
                headings.append({"level": tag, "text": txt})

    noindex = False
    meta_robots = soup.find("meta", attrs={"name": "robots"})
    if meta_robots and isinstance(meta_robots, Tag) and meta_robots.get("content"):
        content_val = meta_robots.get("content", "").lower()
        if "noindex" in content_val or "none" in content_val:
            noindex = True

    return {
        "url": url,
        "title": title,
        "meta_description": meta_desc,
        "text": text,
        "headings": headings,
        "links": list(_extract_links(html, url)),
        "noindex": noindex,
    }


def _is_same_domain(url: str, base_url: str) -> bool:
    return urlparse(url).netloc.lower() == urlparse(base_url).netloc.lower()


def _validate_url_for_crawl(url: str) -> str:
    """Validate URL for crawling with SSRF protection."""
    try:
        return _ssrfer.validate_url_async(url)
    except SSRFProtectionError as exc:
        logger.debug("SSRF validation failed for %s: %s", url, exc)
        raise


class AsyncCrawler:
    """Polite async web crawler with configurable concurrency, depth limits, and callbacks."""

    def __init__(
        self,
        user_agent: str | None = None,
        max_concurrency: int | None = None,
        default_delay: float | None = None,
        max_depth: int | None = None,
        respect_robots: bool = True,
        max_redirects: int | None = None,
    ):
        self._user_agent = user_agent or settings.crawler_user_agent
        self._max_concurrency = max_concurrency or settings.crawler_max_concurrency
        self._default_delay = default_delay or settings.crawler_default_delay
        self._max_depth = max_depth or settings.crawler_max_depth
        self._respect_robots = respect_robots
        self._max_redirects = max_redirects or settings.crawler_max_depth

        self._semaphore = asyncio.Semaphore(self._max_concurrency)
        self._robots = RobotsParser(user_agent=self._user_agent)
        self._domain_timers: dict[str, float] = defaultdict(float)
        self._domain_locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
        self._seen_urls: set[str] = set()
        self._url_callbacks: list[CrawlCallback] = []
        self._content_callbacks: list[ContentCallback] = []
        self._stopped = False

    @property
    def user_agent(self) -> str:
        return self._user_agent

    @property
    def seen_count(self) -> int:
        return len(self._seen_urls)

    def on_url_discovered(self, callback: CrawlCallback):
        self._url_callbacks.append(callback)

    def on_content_extracted(self, callback: ContentCallback):
        self._content_callbacks.append(callback)

    def stop(self):
        self._stopped = True

    async def _respect_rate_limit(self, url: str):
        domain = urlparse(url).netloc.lower()
        async with self._domain_locks[domain]:
            delay = self._default_delay
            if self._respect_robots:
                try:
                    delay = await self._robots.get_crawl_delay(url)
                except Exception as exc:
                    logger.warning("Failed to get crawl delay for %s: %s", url, exc)
            last = self._domain_timers.get(domain, 0.0)
            wait = max(0.0, delay - (asyncio.get_event_loop().time() - last))
            if wait > 0:
                await asyncio.sleep(wait)
            self._domain_timers[domain] = asyncio.get_event_loop().time()

    async def _fetch(self, url: str, client: httpx.AsyncClient) -> str | None:
        if self._respect_robots:
            allowed = await self._robots.can_fetch(url)
            if not allowed:
                logger.debug("Blocked by robots.txt: %s", url)
                return None

        try:
            resp = await client.get(
                url,
                headers={"User-Agent": self._user_agent},
                follow_redirects=False,  # Disabled for SSRF protection
                timeout=httpx.Timeout(30.0),
            )
            
            # Handle redirects manually with SSRF validation
            if resp.status_code in (301, 302, 303, 307, 308):
                location = resp.headers.get("Location", "")
                if not location:
                    logger.debug("Redirect without Location header: %s", url)
                    return None
                
                # Validate redirect URL
                try:
                    validated_url = await _ssrfer.validate_redirect(url, location, 0)
                except SSRFProtectionError as exc:
                    logger.warning("Redirect blocked for %s: %s", url, exc)
                    return None
                
                # Follow the validated redirect
                try:
                    resp = await client.get(
                        validated_url,
                        headers={"User-Agent": self._user_agent},
                        follow_redirects=False,
                        timeout=httpx.Timeout(30.0),
                    )
                    resp.raise_for_status()
                except Exception as exc:
                    logger.debug("Redirect request failed for %s: %s", validated_url, exc)
                    return None
            
            resp.raise_for_status()
            ctype = resp.headers.get("content-type", "").lower()
            if not any(t in ctype for t in _CONTENT_TYPES):
                logger.debug("Skipping non-HTML content: %s (%s)", url, ctype)
                return None
            return resp.text
        except SSRFProtectionError as exc:
            logger.warning("SSRF validation failed for %s: %s", url, exc)
            return None
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code in (301, 302, 303, 307, 308):
                logger.debug("Redirect handled separately for %s", url)
            else:
                logger.warning("HTTP error for %s: %s", url, exc)
            return None
        except httpx.RequestError as exc:
            logger.warning("Request error for %s: %s", url, exc)
            return None
        except asyncio.TimeoutError:
            logger.warning("Timeout fetching %s", url)
            return None
        except Exception as exc:
            logger.warning("Unexpected fetch error for %s: %s", url, exc)
            return None

    async def crawl_page(self, url: str, depth: int, client: httpx.AsyncClient) -> list[str]:
        if self._stopped:
            return []
        
        try:
            # Validate URL for SSRF before processing
            validated_url = await _ssrfer.validate_url_async(url)
            norm_url = normalize_url(validated_url)
        except SSRFProtectionError as exc:
            logger.warning("SSRF validation failed for %s: %s", url, exc)
            return []
        
        if norm_url in self._seen_urls:
            return []
        self._seen_urls.add(norm_url)

        if depth > self._max_depth:
            return []

        if _URL_BLACKLIST.search(norm_url):
            return []

        async with self._semaphore:
            await self._respect_rate_limit(norm_url)

            html = None
            try:
                async for attempt in AsyncRetrying(
                    stop=stop_after_attempt(3),
                    wait=wait_exponential(multiplier=1, min=1, max=10),
                    retry=retry_if_exception_type(
                        (httpx.HTTPStatusError, httpx.RequestError, httpx.TimeoutException)
                    ),
                ):
                    with attempt:
                        html = await self._fetch(norm_url, client)
            except SSRFProtectionError as exc:
                logger.warning("SSRF validation failed for %s after retries: %s", norm_url, exc)
                return []
            except Exception as exc:
                logger.warning("Failed to fetch %s after retries: %s", norm_url, exc)
                return []

            if html is None:
                return []

            try:
                extracted = extract_content(html, norm_url)
            except Exception as exc:
                logger.warning("Content extraction failed for %s: %s", norm_url, exc)
                return []

            extracted["depth"] = depth
            extracted["crawled_at"] = datetime.now(timezone.utc).isoformat()

            for cb in self._content_callbacks:
                try:
                    await cb(extracted)
                except Exception as exc:
                    logger.error("Content callback error for %s: %s", norm_url, exc)

            discovered = []
            if depth < self._max_depth:
                for link in extracted.get("links", []):
                    try:
                        # Re-validate each discovered link for SSRF
                        validated_link = await _ssrfer.validate_url_async(link)
                        if validated_link not in self._seen_urls:
                            discovered.append(validated_link)
                            for cb in self._url_callbacks:
                                try:
                                    await cb(validated_link)
                                except Exception as exc:
                                    logger.error("URL callback error for %s: %s", validated_link, exc)
                    except SSRFProtectionError as exc:
                        logger.debug("SSRF blocked discovered link %s: %s", link, exc)
                        continue

            return discovered

    async def crawl(self, start_urls: list[str], max_pages: int = 100) -> list[dict]:
        self._stopped = False
        self._seen_urls.clear()
        results: list[dict] = []
        queue: list[tuple[str, int]] = []
        
        # Pre-validate all start URLs
        for u in start_urls:
            try:
                validated = await _ssrfer.validate_url_async(u)
                queue.append((validated, 0))
            except SSRFProtectionError as exc:
                logger.warning("SSRF validation failed for start URL %s: %s", u, exc)
        
        pages_crawled = 0

        async def on_content(data: dict):
            nonlocal pages_crawled
            results.append(data)
            pages_crawled += 1

        self._content_callbacks.append(on_content)

        async with httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            limits=httpx.Limits(max_keepalive_connections=self._max_concurrency),
        ) as client:
            while queue and pages_crawled < max_pages and not self._stopped:
                url, depth = queue.pop(0)
                discovered = await self.crawl_page(url, depth, client)
                for link in discovered:
                    if len(queue) + pages_crawled < max_pages:
                        queue.append((link, depth + 1))

        self._content_callbacks.remove(on_content)
        return results

    async def crawl_with_queue(
        self,
        queue: list[tuple[str, int]],
        max_pages: int,
        on_crawled: ContentCallback | None = None,
        on_url: CrawlCallback | None = None,
    ) -> list[dict]:
        if on_crawled:
            self.on_content_extracted(on_crawled)
        if on_url:
            self.on_url_discovered(on_url)
        
        # Pre-validate all queue URLs
        validated_queue = []
        for url, depth in queue:
            try:
                validated = await _ssrfer.validate_url_async(url)
                validated_queue.append((validated, depth))
            except SSRFProtectionError as exc:
                logger.warning("SSRF validation failed for queue URL %s: %s", url, exc)
        
        return await self.crawl([u for u, _ in validated_queue], max_pages=max_pages)