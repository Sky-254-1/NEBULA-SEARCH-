"""SSRF regression tests for crawler destinations and redirects."""

import socket

import httpx
import pytest

from app.crawler.crawler import AsyncCrawler


@pytest.mark.asyncio
async def test_crawler_rejects_private_initial_destination():
    calls = []

    async def handler(request: httpx.Request):
        calls.append(request.url)
        return httpx.Response(200, text="<html>ok</html>", request=request)

    crawler = AsyncCrawler(respect_robots=False)
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await crawler._fetch("http://127.0.0.1/private", client)

    assert result is None
    assert calls == []


@pytest.mark.asyncio
async def test_crawler_rejects_private_url_before_robots_lookup():
    crawler = AsyncCrawler(respect_robots=True)

    async def unexpected_robots_request(url):
        raise AssertionError("robots lookup must not run for a private URL")

    crawler._robots.can_fetch = unexpected_robots_request
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda request: None)) as client:
        discovered = await crawler.crawl_page("http://127.0.0.1/private", 0, client)

    assert discovered == []


@pytest.mark.asyncio
async def test_crawler_revalidates_redirect_destination(monkeypatch):
    calls = []

    def public_dns(host, port, type):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", port))]

    monkeypatch.setattr("app.crawler.security.socket.getaddrinfo", public_dns)

    async def handler(request: httpx.Request):
        calls.append(request.url)
        return httpx.Response(
            302,
            headers={"Location": "http://127.0.0.1/admin"},
            request=request,
        )

    crawler = AsyncCrawler(respect_robots=False)
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await crawler._fetch("https://public.example/article", client)

    assert result is None
    assert [str(url) for url in calls] == ["https://public.example/article"]


@pytest.mark.asyncio
async def test_crawler_fetches_public_destination(monkeypatch):
    def public_dns(host, port, type):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", port))]

    monkeypatch.setattr("app.crawler.security.socket.getaddrinfo", public_dns)

    async def handler(request: httpx.Request):
        return httpx.Response(
            200,
            headers={"Content-Type": "text/html"},
            text="<html>public content</html>",
            request=request,
        )

    crawler = AsyncCrawler(respect_robots=False)
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await crawler._fetch("https://public.example/article", client)

    assert result == "<html>public content</html>"
