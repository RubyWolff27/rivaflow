"""API versioning middleware for backward compatibility."""
from fastapi import Request
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware


class VersioningMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle API versioning with backward compatibility.

    Redirects /api/* requests to /api/v1/* to maintain backward compatibility
    while new clients can use versioned endpoints directly.
    """

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Redirect old /api/* paths to /api/v1/* (except /api/v1 itself)
        if path.startswith("/api/") and not path.startswith("/api/v1/"):
            # Extract the part after /api/
            suffix = path[5:]  # Remove "/api/"

            # Build new versioned path
            new_path = f"/api/v1/{suffix}"

            # Preserve query string if present
            query_string = request.url.query
            if query_string:
                new_url = f"{new_path}?{query_string}"
            else:
                new_url = new_path

            # Use 307 to preserve the HTTP method (POST, PUT, DELETE, etc.)
            return RedirectResponse(url=new_url, status_code=307)

        # Process request normally
        response = await call_next(request)
        return response
