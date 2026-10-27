"""SSRF protection for web crawler.

Provides URL validation, DNS resolution validation, and SSRF prevention
for all crawler HTTP requests.
"""

import asyncio
import logging
import re
import socket
from ipaddress import IPv4Address, IPv4Network, IPv6Address, IPv6Network
from typing import Optional, Tuple
from urllib.parse import urlparse, urljoin, urlunparse

logger = logging.getLogger("nebula.crawler.ssrf")

# Cloud metadata endpoints that should never be accessed
CLOUD_METADATA_ENDPOINTS = {
    # AWS
    "169.254.169.254",
    "100.100.100.200",
    "metadata.google.internal",
    "metadata.azure.com",
    "169.254.169.254",
    # GCP
    "metadata.google.internal",
    "169.254.169.254",
    # Azure
    "169.254.169.254",
    "metadata.azure.com",
    # Alibaba Cloud
    "100.100.100.200",
}

# Private, loopback, and reserved IP ranges
PRIVATE_IPV4_NETWORKS = [
    IPv4Network("0.0.0.0/8"),        # Current network (but 0.0.0.0 is special)
    IPv4Network("10.0.0.0/8"),       # Private
    IPv4Network("100.64.0.0/10"),    # CGNAT
    IPv4Network("172.16.0.0/12"),    # Private
    IPv4Network("192.168.0.0/16"),   # Private
    IPv4Network("127.0.0.0/8"),      # Loopback
    IPv4Network("169.254.0.0/16"),   # Link-local
    IPv4Network("192.0.0.0/24"),     # IETF protocol assignments
    IPv4Network("192.0.2.0/24"),     # TEST-NET-1
    IPv4Network("198.51.100.0/24"),  # TEST-NET-2
    IPv4Network("203.0.113.0/24"),   # TEST-NET-3
    IPv4Network("224.0.0.0/4"),      # Multicast
    IPv4Network("240.0.0.0/4"),      # Reserved / Reserved for future use
]

PRIVATE_IPV6_NETWORKS = [
    IPv6Network("::1/128"),          # Loopback
    IPv6Network("fc00::/7"),         # Unique local address (ULA)
    IPv6Network("fe80::/10"),        # Link-local
    IPv6Network("ff00::/8"),         # Multicast
    IPv6Network("::ffff:0:0/96"),    # IPv4-mapped
    IPv6Network("2001:db8::/32"),    # Documentation
    IPv6Network("::/128"),           # Unspecified
    IPv6Network("2001:10::/28"),     # ORCHID (deprecated)
    IPv6Network("2001:20::/28"),     # ORCHIDv2 (deprecated)
    IPv6Network("2001:30::/28"),     # ORCHIDv2 (deprecated)
    IPv6Network("2001:40::/28"),     # ORCHIDv2 (deprecated)
    IPv6Network("2001:50::/28"),     # ORCHIDv2 (deprecated)
    IPv6Network("2001:60::/28"),     # ORCHIDv2 (deprecated)
    IPv6Network("2001:70::/28"),     # ORCHIDv2 (deprecated)
    IPv6Network("2001:80::/28"),     # ORCHIDv2 (deprecated)
    IPv6Network("2001:90::/28"),     # ORCHIDv2 (deprecated)
    IPv6Network("2001:a0::/28"),     # ORCHIDv2 (deprecated)
    IPv6Network("2001:b0::/28"),     # ORCHIDv2 (deprecated)
    IPv6Network("2001:c0::/28"),     # ORCHIDv2 (deprecated)
    IPv6Network("2001:d0::/28"),     # ORCHIDv2 (deprecated)
    IPv6Network("2001:e0::/28"),     # ORCHIDv2 (deprecated)
    IPv6Network("2001:f0::/28"),     # ORCHIDv2 (deprecated)
    IPv6Network("2002::/16"),        # 6to4
    IPv6Network("2001::/32"),        # TEREDO
]


class SSRFProtectionError(Exception):
    """Raised when a URL is blocked due to SSRF protection."""
    pass


def is_ip_address(host: str) -> bool:
    """Check if host is an IP address (IPv4 or IPv6)."""
    try:
        IPv4Address(host)
        return True
    except ValueError:
        try:
            IPv6Address(host)
            return True
        except ValueError:
            return False


def is_ipv4_mapped_ipv6(host: str) -> bool:
    """Check if host is an IPv4-mapped IPv6 address."""
    try:
        addr = IPv6Address(host)
        return addr.ipv4_mapped is not None
    except ValueError:
        return False


def get_ipv4_from_mapped(host: str) -> str:
    """Extract IPv4 address from IPv4-mapped IPv6 address."""
    try:
        addr = IPv6Address(host)
        if addr.ipv4_mapped:
            return str(addr.ipv4_mapped)
    except ValueError:
        pass
    return host


def is_cloud_metadata_endpoint(host: str) -> bool:
    """Check if host is a known cloud metadata endpoint."""
    # Normalize host for comparison
    host_lower = host.lower().rstrip('.')
    
    # Check exact match
    if host_lower in CLOUD_METADATA_ENDPOINTS:
        return True
    
    # Check if any metadata endpoint is a suffix (e.g., sub.metadata.google.internal)
    for endpoint in CLOUD_METADATA_ENDPOINTS:
        if host_lower.endswith('.' + endpoint):
            return True
    
    return False


def is_private_ipv4(host: str) -> bool:
    """Check if IPv4 address is private, loopback, or reserved."""
    try:
        addr = IPv4Address(host)
        
        # Check cloud metadata endpoints
        if str(addr) in CLOUD_METADATA_ENDPOINTS:
            return True
        
        # Check each private/reserved network
        for network in PRIVATE_IPV4_NETWORKS:
            if addr in network:
                return True
        
        return False
    except ValueError:
        return False


def is_private_ipv6(host: str) -> bool:
    """Check if IPv6 address is private, loopback, or reserved."""
    try:
        addr = IPv6Address(host)
        
        # Check IPv4-mapped IPv6
        if addr.ipv4_mapped:
            mapped_ipv4 = str(addr.ipv4_mapped)
            return is_private_ipv4(mapped_ipv4)
        
        # Check each private/reserved network
        for network in PRIVATE_IPV6_NETWORKS:
            if addr in network:
                return True
        
        return False
    except ValueError:
        return False


def is_private_ip(host: str) -> bool:
    """Check if host is a private, loopback, or reserved IP address."""
    if not host:
        return True
    
    # Check if IPv4
    if '.' in host and ':' not in host:
        return is_private_ipv4(host)
    
    # Check if IPv6 or IPv4-mapped
    if ':' in host:
        return is_private_ipv6(host)
    
    return False


def is_unsafe_ip(host: str) -> bool:
    """Check if host resolves to any unsafe IP address."""
    # First check if it's an IP address directly
    if is_ip_address(host):
        return is_private_ip(host)
    
    # For hostnames, we need DNS resolution to check IPs
    return False  # Will be checked after DNS resolution


def normalize_host(host: str) -> str:
    """Normalize hostname for comparison."""
    if not host:
        return ""
    
    # Convert to lowercase
    host = host.lower()
    
    # Remove trailing dot (FQDN)
    if host.endswith('.'):
        host = host[:-1]
    
    return host


def validate_url(url: str, allow_schemes: Tuple[str, ...] = ("http", "https")) -> str:
    """
    Validate a URL for SSRF protection.
    
    Args:
        url: The URL to validate
        allow_schemes: Tuple of allowed schemes (default: http, https)
    
    Returns:
        The normalized, validated URL
    
    Raises:
        SSRFProtectionError: If URL fails validation
    """
    if not url:
        raise SSRFProtectionError("URL is empty")
    
    try:
        parsed = urlparse(url)
    except Exception as exc:
        raise SSRFProtectionError(f"URL parsing failed: {exc}")
    
    # Validate scheme
    scheme = parsed.scheme.lower()
    if scheme not in allow_schemes:
        raise SSRFProtectionError(f"Scheme '{scheme}' not allowed (allowed: {allow_schemes})")
    
    # Validate netloc (host:port)
    if not parsed.netloc:
        raise SSRFProtectionError("URL missing host")
    
    # Extract and validate host
    host = parsed.hostname
    if not host:
        raise SSRFProtectionError("URL missing host")
    
    host = normalize_host(host)
    
    # Reject cloud metadata endpoints
    if is_cloud_metadata_endpoint(host):
        raise SSRFProtectionError(f"Access to cloud metadata endpoint blocked: {host}")

    # Reject literal private/reserved IP addresses. Hostnames that resolve to
    # private addresses are handled by ``resolve_and_validate_host``.
    if is_ip_address(host) and is_private_ip(host):
        raise SSRFProtectionError(f"Private/reserved IP address blocked: {host}")
    
    # Reject embedded credentials (user:pass@host)
    if parsed.username:
        raise SSRFProtectionError("URL contains embedded credentials")
    
    if parsed.password:
        raise SSRFProtectionError("URL contains embedded credentials")
    
    # Validate port if specified. ``urlparse`` raises ``ValueError`` for ports
    # outside 0-65535 (or non-numeric ones), which must surface as an SSRF
    # rejection rather than an unhandled exception.
    try:
        port = parsed.port
    except ValueError:
        raise SSRFProtectionError(f"Invalid port in URL: {url}")
    if port is not None:
        # Reject non-standard ports (optional security measure)
        if port < 1 or port > 65535:
            raise SSRFProtectionError(f"Invalid port: {port}")
        # Optional: block common non-web ports
        blocked_ports = {
            21,   # FTP
            22,   # SSH
            23,   # Telnet
            25,   # SMTP
            53,   # DNS
            69,   # TFTP
            110,  # POP3
            143,  # IMAP
            389,  # LDAP
            445,  # SMB
            512,  # rexec
            513,  # rlogin
            514,  # rsh
            873,  # rsync
            11211,  # Memcached
            27017,  # MongoDB
            6379,   # Redis
            9200,   # Elasticsearch
            9300,   # Elasticsearch transport
        }
        if port in blocked_ports:
            raise SSRFProtectionError(f"Access to port {port} blocked")
    
    # Normalize URL
    normalized = parsed._replace(netloc=host)
    if port:
        normalized = parsed._replace(netloc=f"{host}:{port}")
    
    return urlunparse(normalized)


async def resolve_and_validate_host(
    host: str,
    loop: asyncio.AbstractEventLoop | None = None,
) -> list[str]:
    """
    Resolve hostname to IP addresses and validate all addresses.
    
    Args:
        host: The hostname to resolve
        loop: Asyncio event loop (default: get_event_loop)
    
    Returns:
        List of valid IP addresses
    
    Raises:
        SSRFProtectionError: If resolution fails or any IP is unsafe
    """
    if loop is None:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:  # pragma: no cover - no running loop in this thread
            loop = asyncio.get_event_loop()

    if not host:
        raise SSRFProtectionError("Empty hostname")

    host = normalize_host(host)

    # If already an IP address, validate it directly
    if is_ip_address(host):
        if is_private_ip(host):
            raise SSRFProtectionError(f"Private/reserved IP address blocked: {host}")
        return [host]

    # Resolve hostname to IP addresses. ``family``/``type`` are keyword-only
    # arguments on asyncio's ``getaddrinfo``.
    try:
        info = await loop.getaddrinfo(
            host,
            None,
            family=socket.AF_UNSPEC,
            type=socket.SOCK_STREAM,
        )
    except socket.gaierror as exc:
        raise SSRFProtectionError(f"DNS resolution failed: {exc}")
    except Exception as exc:
        raise SSRFProtectionError(f"DNS resolution error: {exc}")
    
    if not info:
        raise SSRFProtectionError("DNS resolution returned no addresses")
    
    # Extract unique IP addresses
    ip_addresses = []
    seen_ips = set()
    
    for family, socktype, proto, canonname, sockaddr in info:
        ip = sockaddr[0]
        
        # Skip duplicates
        if ip in seen_ips:
            continue
        seen_ips.add(ip)
        
        # Validate each IP address
        if is_private_ip(ip):
            raise SSRFProtectionError(
                f"Hostname '{host}' resolves to unsafe IP address: {ip}"
            )
        
        ip_addresses.append(ip)
    
    if not ip_addresses:
        raise SSRFProtectionError(f"No valid IP addresses resolved for hostname: {host}")
    
    return ip_addresses


def urlunparse(components: Tuple) -> str:
    """Custom urlunparse to handle normalized netloc."""
    scheme, netloc, path, params, query, fragment = components
    
    # Ensure proper URL format
    if not path:
        path = "/"
    
    return f"{scheme}://{netloc}{path}{params if params else ''}{query if query else ''}{fragment if fragment else ''}"


class SSRFValidator:
    """SSRF validation service for crawler."""
    
    def __init__(
        self,
        max_redirects: int = 5,
        allow_http_downgrade: bool = False,
    ):
        self.max_redirects = max_redirects
        self.allow_http_downgrade = allow_http_downgrade
    
    def is_safe_url(self, url: str) -> bool:
        """Check if URL is safe to crawl (synchronous version)."""
        try:
            validate_url(url)
            return True
        except SSRFProtectionError:
            return False
    
    async def validate_url_async(self, url: str) -> str:
        """Validate URL with async DNS resolution."""
        # First validate URL structure
        normalized = validate_url(url)
        parsed = urlparse(normalized)
        
        # Resolve and validate DNS
        await resolve_and_validate_host(parsed.hostname)
        
        return normalized
    
    async def validate_redirect(
        self,
        current_url: str,
        location: str,
        redirect_count: int,
    ) -> str:
        """
        Validate a redirect target URL.
        
        Args:
            current_url: The current URL being crawled
            location: The Location header value
            redirect_count: Current number of redirects
        
        Returns:
            The validated absolute URL
        
        Raises:
            SSRFProtectionError: If redirect is unsafe
        """
        # Check redirect count
        if redirect_count >= self.max_redirects:
            raise SSRFProtectionError(
                f"Maximum redirect count ({self.max_redirects}) exceeded"
            )
        
        # Resolve relative URLs
        try:
            absolute_url = urljoin(current_url, location)
        except Exception as exc:
            raise SSRFProtectionError(f"Failed to resolve redirect URL: {exc}")
        
        # Normalize
        absolute_url = normalize_url(absolute_url)
        
        # Validate the absolute URL
        try:
            validated = await self.validate_url_async(absolute_url)
        except SSRFProtectionError as exc:
            raise SSRFProtectionError(f"Redirect blocked: {exc}")
        
        # Check for HTTPS to HTTP downgrade if disallowed
        if not self.allow_http_downgrade:
            current_scheme = urlparse(current_url).scheme.lower()
            redirect_scheme = urlparse(absolute_url).scheme.lower()
            
            if current_scheme == "https" and redirect_scheme == "http":
                raise SSRFProtectionError(
                    "HTTPS to HTTP downgrade not allowed"
                )
        
        return validated
    
    def is_safe_redirect_status(self, status_code: int) -> bool:
        """Check if status code is a valid redirect status."""
        return status_code in (301, 302, 303, 307, 308)
    
    def get_host(self, url: str) -> str:
        """Extract hostname from URL."""
        parsed = urlparse(url)
        return normalize_host(parsed.hostname or "")
    
    def clear_cache(self):
        """Clear resolved IP cache (no-op, no caching implemented)."""
        pass


def normalize_url(url: str) -> str:
    """Normalize URL for comparison."""
    parsed = urlparse(url.strip())
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    
    # Remove default ports
    if (scheme == "http" and parsed.port == 80) or (scheme == "https" and parsed.port == 443):
        netloc = parsed.hostname or netloc
    
    path = parsed.path
    if path == "":
        path = "/"
    elif path != "/" and path.endswith("/"):
        path = path.rstrip("/")
    
    # Sort query parameters
    query = ""
    if parsed.query:
        params = parsed.query.split("&")
        params = [p for p in params if p]  # Remove empty
        params.sort()
        query = "?" + "&".join(params)
    
    return urlunparse((scheme, netloc, path, parsed.params, query, parsed.fragment))