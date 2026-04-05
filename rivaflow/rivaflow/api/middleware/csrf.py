"""CSRF protection middleware using the double-submit cookie pattern.

Refresh tokens are stored in httpOnly cookies with SameSite=None (mobile
Safari requirement), so mutating endpoints that rely on cookie-based auth
(POST /auth/refresh, POST /auth/logout) are vulnerable to cross-site
request forgery. This middleware mitigates that risk by requiring a
matching CSRF token on all state-changing requests.

Flow:
1. On login / register the backend sets a non-httpOnly cookie ``csrf_token``
   (readable by JavaScript) alongside the httpOnly refresh cookie.
2. The frontend reads ``csrf_token`` from the cookie and attaches it as the
   ``X-CSRF-Token`` header on every POST / PUT / DELETE request.
3. This middleware validates that the header value matches the cookie value.
   A cross-origin attacker can cause the browser to *send* the cookie but
   cannot *read* it to populate the header, so the check blocks CSRF.

Safe (GET/HEAD/OPTIONS) methods are exempt.
Only UNAUTHENTICATED mutating endpoints are exempt from CSRF validation:
``/auth/login``, ``/auth/register``, ``/auth/forgot-password``,
``/auth/reset-password``, and ``/waitlist``. Health-check and webhook
endpoints are also exempt (webhooks use signature validation instead).

IMPORTANT: ``/auth/refresh`` is NOT exempt. It's the exact endpoint CSRF
was built to protect — it uses the httpOnly rf_token cookie to mint a new
access token, so a cross-site POST with SameSite=None cookies could trigger
unauthorized token refresh. The frontend's auth client (web/src/api/auth.ts)
already sends the X-CSRF-Token header on refresh calls. Do not re-add
/auth/refresh to the exempt list.
"""

import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger(__name__)

# Methods that never mutate state — always exempt.
_SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})

# Path prefixes that are exempt from CSRF validation. These are all either
# UNAUTHENTICATED endpoints or non-browser transports (webhook signatures).
# Must be exact API paths or prefixes that are not substrings of any
# authenticated route — see _is_exempt() for the matching rule.
#
# 2026-04-05 Sage: removed "/auth/refresh" (Pentester H-2 — actively
# exploitable CSRF hole). Changed matching from substring `in` to
# startswith/exact (Pentester H-1 — prevents future substring collisions
# like /api/v1/webhooks-settings bypassing CSRF).
_EXEMPT_PREFIXES = (
    "/auth/login",
    "/auth/register",
    "/auth/forgot-password",
    "/auth/reset-password",
    "/waitlist",
    "/health",
    "/webhooks",
)


def _is_exempt(path: str) -> bool:
    """Return True if *path* is exempt from CSRF validation.

    Matches each exempt prefix as a COMPLETE path segment (or chain of
    segments), not a substring. This prevents routes like
    ``/api/v1/webhooks-settings`` from inheriting exemption from the
    ``/webhooks`` prefix.

    Implementation: append "/" to the path, then check whether
    "prefix/" appears as a substring. The trailing slash guarantees we
    only match at a segment boundary:
      - "/api/v1/auth/login" + "/" → "/api/v1/auth/login/"
        contains "/auth/login/" → exempt ✓
      - "/api/v1/waitlist-admin" + "/" → "/api/v1/waitlist-admin/"
        does NOT contain "/waitlist/" → NOT exempt ✓
      - "/api/v1/webhooks/stripe" + "/" → "/api/v1/webhooks/stripe/"
        contains "/webhooks/" → exempt ✓
      - "/healthcheck" + "/" → "/healthcheck/"
        does NOT contain "/health/" → NOT exempt ✓
    """
    path_with_trailing = path if path.endswith("/") else path + "/"
    for prefix in _EXEMPT_PREFIXES:
        if (prefix + "/") in path_with_trailing:
            return True
    return False


class CSRFMiddleware(BaseHTTPMiddleware):
    """Validate the double-submit CSRF token on mutating requests."""

    async def dispatch(self, request: Request, call_next) -> Response:
        # Safe methods and exempt paths skip validation.
        if request.method in _SAFE_METHODS or _is_exempt(request.url.path):
            return await call_next(request)  # type: ignore[no-any-return]

        # Bearer token auth (mobile/API clients) is not vulnerable to CSRF —
        # an attacker cannot forge the Authorization header cross-origin.
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            return await call_next(request)  # type: ignore[no-any-return]

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

        return await call_next(request)  # type: ignore[no-any-return]
