"""CSRF protection middleware using the double-submit cookie pattern.

Now that refresh tokens are stored in httpOnly cookies, mutating endpoints
that rely on cookie-based auth (POST /auth/refresh, POST /auth/logout) are
vulnerable to cross-site request forgery.  This middleware mitigates that
risk by requiring a matching CSRF token on all state-changing requests.

Flow:
1. On login / register the backend sets a non-httpOnly cookie ``csrf_token``
   (readable by JavaScript) alongside the httpOnly refresh cookie.
2. The frontend reads ``csrf_token`` from the cookie and attaches it as the
   ``X-CSRF-Token`` header on every POST / PUT / DELETE request.
3. This middleware validates that the header value matches the cookie value.
   A cross-origin attacker can cause the browser to *send* the cookie but
   cannot *read* it to populate the header, so the check blocks CSRF.

Safe (GET/HEAD/OPTIONS) methods are exempt.
The ``/auth/login``, ``/auth/register``, ``/auth/forgot-password``,
``/auth/reset-password``, and ``/waitlist`` endpoints are exempt because
they are unauthenticated.
Health-check and webhook endpoints are also exempt.
"""

import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger(__name__)

# Methods that never mutate state — always exempt.
_SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})

# Path prefixes/suffixes that are exempt from CSRF validation.
# These are either unauthenticated or use non-browser transports.
_EXEMPT_PATHS = (
    "/auth/login",
    "/auth/register",
    "/auth/refresh",
    "/auth/forgot-password",
    "/auth/reset-password",
    "/waitlist",
    "/health",
    "/webhooks",
)


def _is_exempt(path: str) -> bool:
    """Return True if *path* is exempt from CSRF validation."""
    for exempt in _EXEMPT_PATHS:
        if exempt in path:
            return True
    return False


class CSRFMiddleware(BaseHTTPMiddleware):
    """Validate the double-submit CSRF token on mutating requests."""

    async def dispatch(self, request: Request, call_next) -> Response:
        # Safe methods and exempt paths skip validation.
        if request.method in _SAFE_METHODS or _is_exempt(request.url.path):
            return await call_next(request)

        # Bearer token auth (mobile/API clients) is not vulnerable to CSRF —
        # an attacker cannot forge the Authorization header cross-origin.
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            return await call_next(request)

        # Read the cookie value and the header value.
        cookie_token = request.cookies.get("csrf_token")
        header_token = request.headers.get("x-csrf-token")

        if not cookie_token or not header_token:
            logger.warning(
                "CSRF validation failed — missing token (cookie=%s, header=%s) on %s %s",
                bool(cookie_token),
                bool(header_token),
                request.method,
                request.url.path,
            )
            return JSONResponse(
                status_code=403,
                content={
                    "error": {"message": "CSRF token missing", "code": "CSRF_MISSING"}
                },
            )

        if cookie_token != header_token:
            logger.warning(
                "CSRF validation failed — token mismatch on %s %s",
                request.method,
                request.url.path,
            )
            return JSONResponse(
                status_code=403,
                content={
                    "error": {"message": "CSRF token invalid", "code": "CSRF_INVALID"}
                },
            )

        return await call_next(request)
