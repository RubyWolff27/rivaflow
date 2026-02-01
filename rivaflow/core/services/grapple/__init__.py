"""Grapple AI Coach service package."""

# Lazy imports to avoid loading heavy dependencies at module initialization
# Import these directly when needed:
#   from core.services.grapple.llm_client import GrappleLLMClient
#   from core.services.grapple.rate_limiter import GrappleRateLimiter
#   from core.services.grapple.token_monitor import GrappleTokenMonitor

__all__ = [
    "GrappleLLMClient",
    "GrappleRateLimiter",
    "GrappleTokenMonitor",
]
