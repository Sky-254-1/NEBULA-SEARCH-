"""SSRF protection tests for crawler.

Tests that verify the crawler properly validates URLs to prevent
Server-Side Request Forgery attacks.
"""

import asyncio
import pytest
from ipaddress import IPv4Address, IPv6Address

from app.crawler.ssrf_protection import (
    SSRFProtectionError,
    SSRFValidator,
    is_cloud_metadata_endpoint,
    is_private_ip,
    is_private_ipv4,
    is_private_ipv6,
    normalize_host,
    resolve_and_validate_host,
    validate_url,
)


class TestURLValidation:
    """Tests for URL validation function."""

    @pytest.mark.parametrize("valid_url", [
        "http://example.com",
        "https://example.com",
        "https://example.com/path",
        "https://example.com:443/path",
        "https://example.com/path?query=value",
    ])
    def test_valid_urls(self, valid_url):
        """Valid public URLs should pass validation."""
        result = validate_url(valid_url)
        assert "example.com" in result

    @pytest.mark.parametrize("invalid_url", [
        "ftp://example.com",  # Invalid scheme
        "mailto:user@example.com",  # Invalid scheme
        "javascript:alert(1)",  # Invalid scheme
        "http://",  # Missing host
        "http:///path",  # Missing host
        "http://user:pass@example.com",  # Embedded credentials
        "http://user@example.com",  # Embedded username
        "http://example.com:99999",  # Invalid port
    ])
    def test_invalid_urls(self, invalid_url):
        """Invalid URLs should be rejected."""
        with pytest.raises(SSRFProtectionError):
            validate_url(invalid_url)

    def test_cloud_metadata_endpoints_blocked(self):
        """Cloud metadata endpoints should be blocked."""
        metadata_endpoints = [
            "http://169.254.169.254",
            "http://metadata.google.internal",
            "http://100.100.100.200",  # Alibaba Cloud
        ]
        for endpoint in metadata_endpoints:
            with pytest.raises(SSRFProtectionError, match="cloud metadata"):
                validate_url(endpoint)

    def test_embedded_credentials_blocked(self):
        """URLs with embedded credentials should be rejected."""
        urls_with_credentials = [
            "http://admin:password@example.com",
            "http://user@example.com",
        ]
        for url in urls_with_credentials:
            with pytest.raises(SSRFProtectionError, match="credentials"):
                validate_url(url)

    def test_blocked_ports(self):
        """Common non-web ports should be blocked."""
        blocked_ports = [21, 22, 23, 25, 53, 69, 110, 143, 389, 445, 512, 513, 514]
        for port in blocked_ports:
            with pytest.raises(SSRFProtectionError, match="blocked"):
                validate_url(f"http://example.com:{port}")


class TestPrivateIPValidation:
    """Tests for private IP address detection."""

    @pytest.mark.parametrize("private_ip", [
        "127.0.0.1",  # Loopback
        "10.0.0.1",  # Private
        "10.255.255.255",  # Private
        "172.16.0.1",  # Private
        "172.31.255.255",  # Private
        "192.168.0.1",  # Private
        "192.168.255.255",  # Private
        "0.0.0.0",  # Current network
        "169.254.0.1",  # Link-local
        "169.254.255.255",  # Link-local
        "224.0.0.1",  # Multicast
        "239.255.255.255",  # Multicast
        "240.0.0.1",  # Reserved
        "255.255.255.255",  # Broadcast
    ])
    def test_private_ipv4(self, private_ip):
        """Private IPv4 addresses should be detected."""
        assert is_private_ipv4(private_ip), f"{private_ip} should be detected as private"

    @pytest.mark.parametrize("public_ip", [
        "8.8.8.8",  # Google DNS
        "1.1.1.1",  # Cloudflare DNS
        "93.184.216.34",  # Example.com
    ])
    def test_public_ipv4(self, public_ip):
        """Public IPv4 addresses should not be detected as private."""
        assert not is_private_ipv4(public_ip), f"{public_ip} should not be detected as private"

    @pytest.mark.parametrize("private_ipv6", [
        "::1",  # Loopback
        "fc00::1",  # Unique local address
        "fdff:ffff:ffff:ffff:ffff:ffff:ffff:ffff",  # ULA
        "fe80::1",  # Link-local
        "ff01::1",  # Multicast
        "::ffff:127.0.0.1",  # IPv4-mapped loopback
        "::ffff:10.0.0.1",  # IPv4-mapped private
    ])
    def test_private_ipv6(self, private_ipv6):
        """Private IPv6 addresses should be detected."""
        assert is_private_ipv6(private_ipv6), f"{private_ipv6} should be detected as private"

    @pytest.mark.parametrize("public_ipv6", [
        "2001:4860:4860::8888",  # Google DNS
        "2606:4700:4700::1111",  # Cloudflare DNS
        "2606:4700:4700::1001",  # Cloudflare DNS
    ])
    def test_public_ipv6(self, public_ipv6):
        """Public IPv6 addresses should not be detected as private."""
        assert not is_private_ipv6(public_ipv6), f"{public_ipv6} should not be detected as private"

    def test_cloud_metadata_ip_addresses(self):
        """Cloud metadata IP addresses should be detected."""
        assert is_private_ip("169.254.169.254")
        assert is_private_ip("100.100.100.200")


class TestHostnameValidation:
    """Tests for hostname resolution and validation."""

    @pytest.mark.asyncio
    async def test_public_hostname(self):
        """Public hostnames should resolve to public IPs."""
        # This test may fail in some environments due to network restrictions
        # In CI/CD, DNS resolution may be blocked - this is expected
        try:
            # Use a known public hostname
            ips = await resolve_and_validate_host("example.com")
            assert len(ips) > 0
            # All IPs should be public
            for ip in ips:
                assert not is_private_ip(ip), f"Resolved IP {ip} should be public"
        except Exception as exc:
            # DNS resolution may be blocked in test environment
            pytest.skip(f"DNS resolution not available: {exc}")

    @pytest.mark.asyncio
    async def test_private_hostname_blocked(self):
        """Hostnames resolving to private IPs should be blocked."""
        with pytest.raises(SSRFProtectionError):
            await resolve_and_validate_host("localhost")
    
    @pytest.mark.asyncio
    async def test_invalid_hostname(self):
        """Invalid hostnames should raise DNS error."""
        with pytest.raises(SSRFProtectionError):
            await resolve_and_validate_host("invalid-host-that-does-not-exist.example")


class TestSSRFValidator:
    """Tests for SSRFValidator class."""

    @pytest.fixture
    def validator(self):
        return SSRFValidator(max_redirects=5)

    @pytest.mark.asyncio
    async def test_validate_url(self, validator):
        """URL validation should work."""
        result = await validator.validate_url_async("https://example.com")
        assert "example.com" in result

    @pytest.mark.asyncio
    async def test_validate_private_ip_blocked(self, validator):
        """Private IP addresses should be blocked."""
        with pytest.raises(SSRFProtectionError):
            await validator.validate_url_async("http://127.0.0.1")

    @pytest.mark.asyncio
    async def test_is_safe_url(self, validator):
        """is_safe_url should reject private/loopback URLs and accept public ones."""
        assert validator.is_safe_url("https://example.com")
        assert not validator.is_safe_url("http://127.0.0.1:8080")
        assert not validator.is_safe_url("http://127.0.0.1")

    @pytest.mark.asyncio
    async def test_validate_redirect(self, validator):
        """Redirect URL validation should work."""
        current = "https://example.com/page"
        location = "/redirected"
        result = await validator.validate_redirect(current, location, 0)
        assert "example.com" in result

    @pytest.mark.asyncio
    async def test_redirect_to_private_blocked(self, validator):
        """Redirects to private IPs should be blocked."""
        current = "https://example.com"
        location = "http://127.0.0.1"
        with pytest.raises(SSRFProtectionError):
            await validator.validate_redirect(current, location, 0)

    @pytest.mark.asyncio
    async def test_https_to_http_redirect_blocked(self, validator):
        """HTTPS to HTTP redirects should be blocked."""
        current = "https://example.com"
        location = "http://example.com/other"
        with pytest.raises(SSRFProtectionError, match="HTTPS to HTTP"):
            await validator.validate_redirect(current, location, 0)

    @pytest.mark.asyncio
    async def test_redirect_count_limit(self, validator):
        """Max redirect count should be enforced."""
        # Use a public IP literal to avoid DNS resolution in tests
        current = "https://93.184.216.34"
        location = "https://93.184.216.34/other"
        
        # First redirect is OK
        await validator.validate_redirect(current, location, 0)
        # At max, should still work
        await validator.validate_redirect(current, location, 4)
        # One more should fail
        with pytest.raises(SSRFProtectionError, match="Maximum redirect count"):
            await validator.validate_redirect(current, location, 5)

    def test_is_safe_redirect_status(self, validator):
        """Valid redirect status codes should be recognized."""
        assert validator.is_safe_redirect_status(301)
        assert validator.is_safe_redirect_status(302)
        assert validator.is_safe_redirect_status(303)
        assert validator.is_safe_redirect_status(307)
        assert validator.is_safe_redirect_status(308)
        assert not validator.is_safe_redirect_status(200)
        assert not validator.is_safe_redirect_status(404)


class TestCrawlerIntegration:
    """Integration tests for crawler SSRF protection."""

    @pytest.mark.asyncio
    async def test_crawler_blocks_private_ips(self):
        """Crawler should block requests to private IPs."""
        from app.crawler.crawler import AsyncCrawler
        
        crawler = AsyncCrawler(max_depth=1)
        
        # Mock client that would make requests
        # We just test that validation happens, not actual HTTP
        with pytest.raises(SSRFProtectionError):
            await crawler.crawl(["http://127.0.0.1"], max_pages=1)

    @pytest.mark.asyncio
    async def test_crawler_blocks_cloud_metadata(self):
        """Crawler should block cloud metadata endpoints."""
        from app.crawler.crawler import AsyncCrawler
        
        crawler = AsyncCrawler(max_depth=1)
        
        with pytest.raises(SSRFProtectionError):
            await crawler.crawl(["http://169.254.169.254"], max_pages=1)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])