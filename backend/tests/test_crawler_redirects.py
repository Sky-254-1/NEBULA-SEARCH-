"""Redirect-level SSRF protection tests for the async crawler."""

import httpx
import pytest

from app.crawler.crawler import AsyncCrawler

# Public IP literal (example.com) so the tests do not depend on DNS.
PUBLIC = "https://93.184.216.34"


class FakeResponse:
    def __init__(self, status_code: int, headers: dict | None = None, text: str = ""):
        self.status_code = status_code
        self.headers = headers or {}
        self.text = text

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            request = httpx.Request("GET", PUBLIC)
            response = httpx.Response(self.status_code, request=request)
            raise httpx.HTTPStatusError("error", request=request, response=response)


class StubClient:
    """Minimal httpx.AsyncClient stand-in that records requested URLs."""

    def __init__(self, responses: list[FakeResponse]):
        self._responses = list(responses)
        self.calls: list[str] = []

    async def get(self, url: str, **kwargs) -> FakeResponse:
        self.calls.append(url)
        if not self._responses:
            raise AssertionError(f"unexpected request to {url}")
        return self._responses.pop(0)


def html_response(text: str = "<html><body>ok</body></html>") -> FakeResponse:
    return FakeResponse(200, {"content-type": "text/html; charset=utf-8"}, text)


@pytest.mark.asyncio
async def test_redirect_chain_is_followed_and_validated():
    crawler = AsyncCrawler(respect_robots=False)
    client = StubClient(
        [
            FakeResponse(302, {"Location": "/next"}),
            html_response(),
        ]
    )

    body = await crawler._fetch(f"{PUBLIC}/start", client)

    assert body is not None and "ok" in body
    assert client.calls == [f"{PUBLIC}/start", f"{PUBLIC}/next"]


@pytest.mark.asyncio
async def test_redirect_to_private_ip_is_blocked():
    crawler = AsyncCrawler(respect_robots=False)
    client = StubClient([FakeResponse(302, {"Location": "http://127.0.0.1/admin"})])

    assert await crawler._fetch(f"{PUBLIC}/start", client) is None
    assert len(client.calls) == 1


@pytest.mark.asyncio
async def test_redirect_to_https_downgrade_is_blocked():
    crawler = AsyncCrawler(respect_robots=False)
    client = StubClient(
        [FakeResponse(301, {"Location": "http://93.184.216.34/insecure"})]
    )

    assert await crawler._fetch(f"{PUBLIC}/start", client) is None
    assert len(client.calls) == 1


@pytest.mark.asyncio
async def test_redirect_count_is_bounded():
    crawler = AsyncCrawler(respect_robots=False, max_redirects=1)
    client = StubClient(
        [
            FakeResponse(302, {"Location": "/a"}),
            FakeResponse(302, {"Location": "/b"}),
            html_response(),
        ]
    )

    assert await crawler._fetch(f"{PUBLIC}/start", client) is None
    assert len(client.calls) == 2


@pytest.mark.asyncio
async def test_non_html_response_is_skipped():
    crawler = AsyncCrawler(respect_robots=False)
    client = StubClient([FakeResponse(200, {"content-type": "application/json"}, "{}")])

    assert await crawler._fetch(f"{PUBLIC}/start", client) is None
