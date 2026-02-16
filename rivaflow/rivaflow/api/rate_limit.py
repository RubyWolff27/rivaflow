"""Shared rate limiter instance for all routes."""

from slowapi import Limiter
from starlette.requests import Request


def _get_real_client_ip(request: Request) -> str:
    """Extract the real client IP, accounting for reverse proxies.

    Render (and most reverse proxies) set X-Forwarded-For with the
    real client IP as the first entry.
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"


limiter = Limiter(key_func=_get_real_client_ip)
