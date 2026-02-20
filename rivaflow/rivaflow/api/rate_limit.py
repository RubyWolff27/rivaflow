"""Shared rate limiter instance for all routes.

X-Forwarded-For trust model
---------------------------
RivaFlow runs behind Render's reverse proxy, which appends the true client
IP as the **rightmost** entry in X-Forwarded-For.  An attacker can spoof
the leftmost entries but cannot control the rightmost one that the proxy
adds.  We therefore always use ``ips[-1]`` (rightmost-1 hop = Render's
append).

If the deployment moves to a multi-proxy chain (e.g. CDN → Render), this
logic must be updated to use rightmost-N where N = number of trusted
proxies.

Note: The rate limiter storage is currently in-process memory
(``slowapi`` default).  This means limits are per-worker, not global.
A Redis backend migration is tracked for a future sprint.
"""

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
