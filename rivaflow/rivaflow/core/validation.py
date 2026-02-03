"""Input validation utilities for security."""
from urllib.parse import urlparse
from typing import Optional


def validate_url(url: str, allowed_schemes: Optional[list] = None) -> bool:
    """
    Validate URL for security.

    Args:
        url: URL string to validate
        allowed_schemes: List of allowed schemes (default: ['https'])

    Returns:
        True if valid, False otherwise

    Raises:
        ValueError: If URL is invalid or uses disallowed scheme
    """
    if allowed_schemes is None:
        allowed_schemes = ['https']  # Only HTTPS by default for security

    try:
        parsed = urlparse(url)

        # Check scheme
        if parsed.scheme not in allowed_schemes:
            raise ValueError(f"URL must use one of: {', '.join(allowed_schemes)}")

        # Check that there's a network location (domain)
        if not parsed.netloc:
            raise ValueError("URL must include a domain")

        # Prevent javascript: and data: URLs (XSS vectors)
        if parsed.scheme in ['javascript', 'data', 'file', 'vbscript']:
            raise ValueError("URL scheme not allowed for security reasons")

        # Basic length check
        if len(url) > 2048:  # RFC 2616 practical limit
            raise ValueError("URL too long")

        return True

    except Exception as e:
        if isinstance(e, ValueError):
            raise
        raise ValueError(f"Invalid URL format: {str(e)}")


def validate_video_url(url: str) -> bool:
    """
    Validate video URL specifically.

    Allows http and https for video platforms, but validates domain.

    Args:
        url: Video URL to validate

    Returns:
        True if valid

    Raises:
        ValueError: If URL is invalid
    """
    # Allow http and https for video platforms
    allowed_schemes = ['https', 'http']

    # Common video platforms (can be expanded)
    trusted_domains = [
        'youtube.com', 'www.youtube.com', 'youtu.be',
        'vimeo.com', 'www.vimeo.com',
        'wistia.com', 'fast.wistia.com',
    ]

    if not validate_url(url, allowed_schemes=allowed_schemes):
        return False

    parsed = urlparse(url)

    # Warn if not from trusted domain (but don't block - let users decide)
    # This is logged for security monitoring
    if not any(parsed.netloc.endswith(domain) for domain in trusted_domains):
        # Log warning but allow - users might use custom video hosting
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Video URL from non-standard domain: {parsed.netloc}")

    return True
