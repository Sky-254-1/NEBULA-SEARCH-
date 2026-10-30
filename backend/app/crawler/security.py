"""Destination checks used by crawler fetches and robots.txt requests."""

import asyncio
import ipaddress
import socket
from urllib.parse import urlparse

_UNSAFE_SERVICE_PORTS = {
    21, 22, 23, 25, 53, 110, 111, 135, 139, 445, 1433, 1521,
    2049, 2375, 2376, 3306, 3389, 5432, 5900, 6379, 9200, 9300,
}


async def is_safe_destination(url: str) -> bool:
    """Allow only HTTP(S) URLs resolving exclusively to public IP addresses."""
    try:
        parsed = urlparse(url)
        scheme = parsed.scheme.lower()
        if scheme not in {"http", "https"} or not parsed.hostname:
            return False
        if parsed.username is not None or parsed.password is not None:
            return False

        host = parsed.hostname.rstrip(".").lower()
        port = parsed.port or (443 if scheme == "https" else 80)
        if port in _UNSAFE_SERVICE_PORTS:
            return False
        try:
            addresses = {ipaddress.ip_address(host)}
        except ValueError:
            records = await asyncio.to_thread(
                socket.getaddrinfo, host, port, type=socket.SOCK_STREAM
            )
            addresses = {ipaddress.ip_address(record[4][0]) for record in records}
        return bool(addresses) and all(address.is_global for address in addresses)
    except (OSError, ValueError, UnicodeError):
        return False
