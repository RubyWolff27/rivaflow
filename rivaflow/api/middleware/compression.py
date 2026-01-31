"""Response compression middleware."""
import gzip
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.datastructures import MutableHeaders


class GzipCompressionMiddleware(BaseHTTPMiddleware):
    """
    Middleware to compress responses with gzip when beneficial.

    Only compresses:
    - Responses larger than 1KB
    - When client accepts gzip encoding
    - JSON and text content types
    """

    MINIMUM_SIZE = 1024  # 1KB minimum
    COMPRESSIBLE_TYPES = {
        "application/json",
        "application/javascript",
        "text/html",
        "text/css",
        "text/plain",
        "text/xml",
    }

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Check if client accepts gzip
        accept_encoding = request.headers.get("accept-encoding", "")
        if "gzip" not in accept_encoding.lower():
            return response

        # Only compress certain content types
        content_type = response.headers.get("content-type", "").split(";")[0]
        if content_type not in self.COMPRESSIBLE_TYPES:
            return response

        # Get response body
        response_body = b""
        async for chunk in response.body_iterator:
            response_body += chunk

        # Only compress if body is large enough
        if len(response_body) < self.MINIMUM_SIZE:
            return Response(
                content=response_body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )

        # Compress the response
        compressed_body = gzip.compress(response_body, compresslevel=6)

        # Create new response with compressed body
        headers = MutableHeaders(response.headers)
        headers["content-encoding"] = "gzip"
        headers["content-length"] = str(len(compressed_body))
        headers["vary"] = "Accept-Encoding"

        return Response(
            content=compressed_body,
            status_code=response.status_code,
            headers=dict(headers),
            media_type=response.media_type,
        )
