"""Shared rate limiter instance for all routes."""

from slowapi import Limiter
from starlette.requests import Request


def _get_real_client_ip(request: Request) -> str:
    """Extract the real client IP, accounting for reverse proxies.

    Uses the rightmost X-Forwarded-For entry (set by our trusted proxy)
    to prevent spoofing via attacker-controlled leftmost entries.
    Falls back to request.client.host when no forwarding header present.
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        # Rightmost entry is from the closest trusted proxy (Render)
        ips = [ip.strip() for ip in forwarded.split(",")]
        return ips[-1] if ips else "127.0.0.1"
    return request.client.host if request.client else "127.0.0.1"


limiter = Limiter(key_func=_get_real_client_ip)
