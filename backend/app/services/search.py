"""Web search provider integrations with SSRF protection."""

import ipaddress
import re
from urllib.parse import quote, urlparse

import httpx
from fastapi import HTTPException

from app.config import get_settings

settings = get_settings()
ALLOWED_BACKENDS = frozenset(
    {"wikipedia", "brave", "serpapi", "google", "bing", "duckduckgo"}
)

# Allowed domains for SSRF protection
ALLOWED_DOMAINS = {
    "en.wikipedia.org",
    "api.search.brave.com",
    "serpapi.com",
    "www.googleapis.com",
    "api.bing.microsoft.com",
    "api.duckduckgo.com",
}

# Block private IP ranges
BLOCKED_IP_RANGES = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("0.0.0.0/8"),
]


def _validate_url(url: str) -> None:
    """Validate URL to prevent SSRF attacks."""
    try:
        parsed = urlparse(url)
        
        # Only allow HTTPS (except localhost for development)
        if parsed.scheme not in ("https", "http"):
            raise HTTPException(status_code=400, detail="Invalid URL scheme")
        
        # Check domain whitelist
        hostname = parsed.hostname
        if not hostname:
            raise HTTPException(status_code=400, detail="Invalid URL: no hostname")
        
        # Allow localhost in development
        if hostname in ("localhost", "127.0.0.1", "::1"):
            if not settings.is_production:
                return
            raise HTTPException(status_code=400, detail="Localhost not allowed in production")
        
        # Check domain whitelist
        if hostname not in ALLOWED_DOMAINS:
            raise HTTPException(status_code=400, detail=f"Domain not allowed: {hostname}")
        
        # Resolve hostname to IP and check if it's private
        try:
            import socket
            ip_str = socket.gethostbyname(hostname)
            ip = ipaddress.ip_address(ip_str)
            
            for network in BLOCKED_IP_RANGES:
                if ip in network:
                    raise HTTPException(
                        status_code=400, 
                        detail="Request to private IP address blocked"
                    )
        except socket.gaierror:
            raise HTTPException(status_code=400, detail="Cannot resolve hostname")
            
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"URL validation failed: {str(exc)}")


def sanitize_query(query: str) -> str:
    """Strip control characters and normalize whitespace."""
    cleaned = re.sub(r"[\x00-\x1f\x7f]", "", query).strip()
    return cleaned


async def search_wikipedia(query: str, page: int, page_size: int) -> list[dict]:
    """Search Wikipedia's public API."""
    offset = (page - 1) * page_size
    encoded = quote(query)
    url = (
        "https://en.wikipedia.org/w/api.php"
        f"?action=query&list=search&srsearch={encoded}"
        f"&srlimit={page_size}&sroffset={offset}"
        "&format=json&origin=*"
    )
    _validate_url(url)
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        data = resp.json()

    results = []
    for item in data.get("query", {}).get("search", []):
        snippet = re.sub(r"<[^>]+>", "", item.get("snippet", ""))
        title = item.get("title", "")
        results.append(
            {
                "title": title,
                "snippet": snippet,
                "url": f"https://en.wikipedia.org/wiki/{quote(title.replace(' ', '_'), safe='')}",
                "source": "wikipedia",
            }
        )
    return results


async def search_brave(query: str, page: int, page_size: int) -> list[dict]:
    """Search via Brave Search API."""
    if not settings.brave_api_key:
        raise HTTPException(status_code=400, detail="Brave API key not configured on server")
    offset = (page - 1) * page_size
    url = (
        "https://api.search.brave.com/res/v1/web/search"
        f"?q={quote(query)}&count={page_size}&offset={offset}"
    )
    _validate_url(url)
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            url,
            headers={
                "X-Subscription-Token": settings.brave_api_key,
                "Accept": "application/json",
            },
        )
        resp.raise_for_status()
        data = resp.json()

    return [
        {
            "title": item.get("title", ""),
            "snippet": item.get("description", ""),
            "url": item.get("url", ""),
            "source": "brave",
        }
        for item in data.get("web", {}).get("results", [])
    ]


async def search_serpapi(query: str, page: int, page_size: int) -> list[dict]:
    """Search via SerpAPI (Google results)."""
    if not settings.serpapi_key:
        raise HTTPException(status_code=400, detail="SerpAPI key not configured on server")
    start = (page - 1) * page_size
    url = "https://serpapi.com/search.json"
    _validate_url(url)
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                url,
                params={
                    "q": query,
                    "api_key": settings.serpapi_key,
                    "engine": "google",
                    "start": start,
                    "num": min(page_size, 100),
                },
            )
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPError:
        # SerpAPI requires the key in the query string; never propagate its URL.
        raise HTTPException(status_code=502, detail="SerpAPI request failed") from None

    return [
        {
            "title": item.get("title", ""),
            "snippet": item.get("snippet", ""),
            "url": item.get("link", ""),
            "source": "serpapi",
        }
        for item in data.get("organic_results", [])
    ]


async def search_google(query: str, page: int, page_size: int) -> list[dict]:
    """Search using Google Custom Search."""
    if not settings.google_api_key or not settings.google_search_cx:
        raise HTTPException(
            status_code=400,
            detail="Google Custom Search API key and search engine ID are not configured",
        )
    result_count = min(page_size, 10)
    url = "https://www.googleapis.com/customsearch/v1"
    _validate_url(url)
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            url,
            headers={"X-Goog-Api-Key": settings.google_api_key},
            params={
                "cx": settings.google_search_cx,
                "q": query,
                "num": result_count,
                "start": (page - 1) * result_count + 1,
            },
        )
        resp.raise_for_status()
        data = resp.json()

    return [
        {
            "title": item.get("title", ""),
            "snippet": item.get("snippet", ""),
            "url": item.get("link", ""),
            "source": "google",
        }
        for item in data.get("items", [])
    ]


async def search_bing(query: str, page: int, page_size: int) -> list[dict]:
    """Search using the Bing Web Search API."""
    if not settings.bing_api_key:
        raise HTTPException(status_code=400, detail="Bing API key not configured on server")
    result_count = min(page_size, 50)
    url = "https://api.bing.microsoft.com/v7.0/search"
    _validate_url(url)
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            url,
            headers={"Ocp-Apim-Subscription-Key": settings.bing_api_key},
            params={
                "q": query,
                "count": result_count,
                "offset": (page - 1) * result_count,
                "textDecorations": False,
                "textFormat": "Raw",
            },
        )
        resp.raise_for_status()
        data = resp.json()

    return [
        {
            "title": item.get("name", ""),
            "snippet": item.get("snippet", ""),
            "url": item.get("url", ""),
            "source": "bing",
        }
        for item in data.get("webPages", {}).get("value", [])
    ]


async def search_duckduckgo(query: str, page: int, page_size: int) -> list[dict]:
    """Search DuckDuckGo's Instant Answer API (no API key required)."""
    url = "https://api.duckduckgo.com/"
    _validate_url(url)
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            url,
            params={
                "q": query,
                "format": "json",
                "no_html": 1,
                "skip_disambig": 1,
            },
        )
        resp.raise_for_status()
        data = resp.json()

    results = []
    if page == 1 and data.get("Abstract"):
        results.append(
            {
                "title": data.get("Heading", query),
                "snippet": data.get("Abstract", ""),
                "url": data.get("AbstractURL", ""),
                "source": "duckduckgo",
            }
        )
    if page == 1:
        for item in data.get("RelatedTopics", []):
            if isinstance(item, dict) and item.get("Text") and item.get("FirstURL"):
                results.append(
                    {
                        "title": item["Text"].split(" - ", 1)[0],
                        "snippet": item["Text"],
                        "url": item["FirstURL"],
                        "source": "duckduckgo",
                    }
                )
                if len(results) >= page_size:
                    break
    return results


async def run_web_search(
    query: str,
    backend: str,
    page: int,
    page_size: int,
) -> list[dict]:
    """Dispatch search to the configured backend."""
    if backend not in ALLOWED_BACKENDS:
        raise HTTPException(status_code=400, detail=f"Unknown backend: {backend}")

    safe_query = sanitize_query(query)
    if not safe_query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    if backend == "wikipedia":
        return await search_wikipedia(safe_query, page, page_size)
    if backend == "brave":
        return await search_brave(safe_query, page, page_size)
    if backend == "serpapi":
        return await search_serpapi(safe_query, page, page_size)
    if backend == "google":
        return await search_google(safe_query, page, page_size)
    if backend == "bing":
        return await search_bing(safe_query, page, page_size)
    return await search_duckduckgo(safe_query, page, page_size)
