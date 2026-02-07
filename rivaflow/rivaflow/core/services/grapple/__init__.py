"""Grapple AI Coach service package."""

# Lazy imports to avoid loading heavy dependencies at module initialization
# Import these directly when needed:
#   from core.services.grapple.llm_client import GrappleLLMClient
#   from core.services.grapple.rate_limiter import GrappleRateLimiter
#   from core.services.grapple.token_monitor import GrappleTokenMonitor
#   from core.services.grapple.session_extraction_service import extract_session_from_text
#   from core.services.grapple.ai_insight_service import generate_post_session_insight
#   from core.services.grapple.glossary_rag_service import technique_qa

__all__ = [
    "GrappleLLMClient",
    "GrappleRateLimiter",
    "GrappleTokenMonitor",
]
