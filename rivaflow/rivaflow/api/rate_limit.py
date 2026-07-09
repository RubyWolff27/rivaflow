"""Shared rate limiter instance for all routes.

Client-IP trust model
---------------------
RivaFlow is fronted by a Cloudflare tunnel (``cloudflared`` in
docker-compose.prod.yml), so the authoritative client IP is the one
Cloudflare sets in ``CF-Connecting-IP`` — a header the origin only ever sees
from Cloudflare and which the client cannot forge past the tunnel. We trust
that first, then fall back to the rightmost ``X-Forwarded-For`` hop (the older
Render topology), then the socket peer.

Historical note: this used to trust only ``X-Forwarded-For[-1]`` for Render's
reverse proxy. Under the current single-CF-tunnel chain that rightmost hop is
the tunnel, not the true client, so every client collapsed onto one key —
weakening every IP-scoped limit, including auth. ``CF-Connecting-IP`` fixes it.

Note: rate-limit storage is in-process memory (``slowapi`` default), so limits
are per-worker, not global. A Redis backend migration is tracked separately.
"""

from slowapi import Limiter
from starlette.requests import Request


def _get_real_client_ip(request: Request) -> str:
    """Extract the real client IP for the Cloudflare-tunnel topology.

    Prefers ``CF-Connecting-IP`` (set by Cloudflare, unforgeable past the
    tunnel), then the rightmost ``X-Forwarded-For`` hop, then the socket peer.
    """
    cf_ip = request.headers.get("cf-connecting-ip")
    if cf_ip and cf_ip.strip():
        return cf_ip.strip()

    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        ips = [ip.strip() for ip in forwarded.split(",") if ip.strip()]
        if ips:
            return ips[-1]
    return request.client.host if request.client else "127.0.0.1"


limiter = Limiter(key_func=_get_real_client_ip)
