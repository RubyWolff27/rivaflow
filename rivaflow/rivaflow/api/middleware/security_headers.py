"""Security headers middleware for production hardening."""

import os

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add security headers to all responses.

    Headers added:
    - Strict-Transport-Security (HSTS): Force HTTPS
    - X-Content-Type-Options: Prevent MIME sniffing
    - X-Frame-Options: Prevent clickjacking
    - X-XSS-Protection: Enable browser XSS protection
    - Referrer-Policy: Control referrer information
    - Content-Security-Policy: Restrict resource loading
    """

    async def dispatch(self, request: Request, call_next):
        """Add security headers to response."""
        response: Response = await call_next(request)

        # Only apply HSTS in production with HTTPS
        env = os.getenv("ENV", "development")
        if env == "production":
            # HSTS: Force HTTPS for 1 year, include subdomains
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # Disable legacy XSS filter (can introduce vulnerabilities in edge cases;
        # modern browsers ignore it, and CSP provides the real protection)
        response.headers["X-XSS-Protection"] = "0"

        # Control referrer information — stricter for auth endpoints
        # to prevent tokens/credentials leaking via Referer header
        path = request.url.path
        if path.startswith("/api/v1/auth") or path.startswith("/api/v1/users/login"):
            response.headers["Referrer-Policy"] = "no-referrer"
        else:
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Content Security Policy - only apply to non-JSON responses
        # API JSON responses don't need CSP; it can cause issues with clients
        content_type = response.headers.get("content-type", "")
        if "application/json" not in content_type:
            # 'unsafe-inline' in style-src is required because Tailwind CSS
            # injects styles at runtime via <style> tags and inline style
            # attributes.  Removing it would break all Tailwind utility
            # classes.  A nonce-based approach is possible but would require
            # server-side rendering of the nonce into every page load, which
            # is non-trivial for our SPA architecture.
            csp_policy = (
                "default-src 'self'; "
                "script-src 'self'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self' https://api.rivaflow.app; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self'"
            )
            response.headers["Content-Security-Policy"] = csp_policy

        # Permissions Policy (formerly Feature-Policy)
        # Disable unnecessary browser features; allow microphone for voice logging
        permissions_policy = (
            "geolocation=(), "
            "microphone=(self), "
            "camera=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "gyroscope=()"
        )
        response.headers["Permissions-Policy"] = permissions_policy

        return response
