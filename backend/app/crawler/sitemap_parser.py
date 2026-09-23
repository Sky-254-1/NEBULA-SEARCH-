"""Sitemap parsing for discovering URLs to crawl."""

import logging
from typing import Set
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger("nebula.crawler.sitemap")


class SitemapParser:
    """Parse XML sitemaps and sitemap indexes to discover URLs."""

    SITEMAP_NS = "http://www.sitemaps.org/schemas/sitemap/0.9"

    async def discover_urls(self, base_url: str, client: httpx.AsyncClient) -> Set[str]:
        """
        Discover URLs from sitemap.xml.
        
        Args:
            base_url: Base URL of the website
            client: HTTP client
            
        Returns:
            Set of discovered URLs
        """
        urls = set()
        parsed = urlparse(base_url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        
        # Try common sitemap locations
        sitemap_paths = [
            "/sitemap.xml",
            "/sitemap_index.xml",
            "/sitemap/sitemap.xml",
        ]
        
        for path in sitemap_paths:
            sitemap_url = urljoin(base, path)
            try:
                resp = await client.get(sitemap_url, timeout=10.0)
                if resp.status_code == 200:
                    content_type = resp.headers.get("content-type", "")
                    if "xml" in content_type or resp.text.strip().startswith("<?xml"):
                        sitemap_urls = await self._parse_sitemap(resp.text, base)
                        urls.update(sitemap_urls)
                        logger.info("Found %d URLs from %s", len(sitemap_urls), sitemap_url)
                        break
            except Exception as exc:
                logger.debug("Failed to fetch sitemap %s: %s", sitemap_url, exc)
        
        return urls

    async def _parse_sitemap(self, xml_content: str, base_url: str) -> Set[str]:
        """Parse sitemap XML and extract URLs."""
        urls = set()
        try:
            soup = BeautifulSoup(xml_content, "xml")
            
            # Check if this is a sitemap index
            sitemap_tags = soup.find_all("sitemap")
            if sitemap_tags:
                # This is a sitemap index, parse each nested sitemap
                for sitemap_tag in sitemap_tags:
                    loc = sitemap_tag.find("loc")
                    if loc and loc.string:
                        nested_url = loc.string.strip()
                        try:
                            async with httpx.AsyncClient(timeout=10.0) as client:
                                resp = await client.get(nested_url)
                                if resp.status_code == 200:
                                    nested_urls = await self._parse_sitemap(resp.text, base_url)
                                    urls.update(nested_urls)
                        except Exception as exc:
                            logger.debug("Failed to parse nested sitemap %s: %s", nested_url, exc)
                return urls
            
            # Regular sitemap with URLs
            url_tags = soup.find_all("url")
            for url_tag in url_tags:
                loc = url_tag.find("loc")
                if loc and loc.string:
                    url = loc.string.strip()
                    # Normalize URL
                    url = self._normalize_url(url, base_url)
                    if url:
                        urls.add(url)
            
            # Alternative format (just <loc> tags)
            if not url_tags:
                loc_tags = soup.find_all("loc")
                for loc in loc_tags:
                    if loc.string:
                        url = loc.string.strip()
                        url = self._normalize_url(url, base_url)
                        if url:
                            urls.add(url)
                            
        except Exception as exc:
            logger.error("Failed to parse sitemap: %s", exc)
        
        return urls

    def _normalize_url(self, url: str, base_url: str) -> str:
        """Normalize and validate URL."""
        try:
            absolute = urljoin(base_url, url)
            parsed = urlparse(absolute)
            
            # Only keep http/https URLs
            if parsed.scheme not in ("http", "https"):
                return ""
            
            # Remove fragment
            normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            if parsed.query:
                normalized += f"?{parsed.query}"
            
            return normalized
        except Exception:
            return ""