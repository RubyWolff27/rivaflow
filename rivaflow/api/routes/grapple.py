"""Grapple AI Coach API routes - Premium BJJ coaching with cloud LLMs."""
import logging
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from rivaflow.core.dependencies import get_current_user
from rivaflow.core.middleware.feature_access import (
    require_beta_or_premium,
    get_user_tier_info,
)

router = APIRouter(prefix="/grapple", tags=["grapple"])
logger = logging.getLogger(__name__)


# ============================================================================
# Request/Response Models
# ============================================================================

class Message(BaseModel):
    """Chat message model."""
    role: str  # 'user', 'assistant', 'system'
    content: str


class ChatRequest(BaseModel):
    """Request to send a message to Grapple."""
    message: str
    session_id: Optional[str] = None  # If None, creates new session


class ChatResponse(BaseModel):
    """Response from Grapple."""
    session_id: str
    message_id: str
    reply: str
    tokens_used: int
    cost_usd: float
    rate_limit_remaining: int


class SessionListResponse(BaseModel):
    """List of chat sessions."""
    sessions: List[dict]


class TierInfoResponse(BaseModel):
    """User's subscription tier and feature access."""
    tier: str
    is_beta: bool
    features: dict
    limits: dict


# ============================================================================
# Teaser Endpoint (Free Users)
# ============================================================================

@router.get("/info", response_model=TierInfoResponse)
async def get_grapple_info(current_user: dict = Depends(get_current_user)):
    """
    Get information about Grapple AI Coach and user's access level.

    This endpoint is available to all authenticated users to show them
    what Grapple is and whether they have access.
    """
    tier_info = get_user_tier_info(current_user)

    return TierInfoResponse(
        tier=tier_info["tier"],
        is_beta=tier_info["is_beta"],
        features=tier_info["features"],
        limits=tier_info["limits"],
    )


@router.get("/teaser")
async def get_grapple_teaser(current_user: dict = Depends(get_current_user)):
    """
    Teaser endpoint showing free users what they're missing.

    Returns information about Grapple features and upgrade path.
    """
    tier = current_user.get('subscription_tier', 'free')
    has_access = tier in ['beta', 'premium', 'admin']

    return {
        "has_access": has_access,
        "current_tier": tier,
        "grapple_features": [
            "🧠 AI-powered BJJ coaching with personalized insights",
            "📊 Context-aware advice based on your training history",
            "🎯 Technique analysis and recommendations",
            "💪 Recovery and progression guidance",
            "📚 Access to curated BJJ knowledge base",
            "⚡ Powered by advanced cloud LLMs (Groq/Together AI)",
        ],
        "beta_features": [
            "✨ 30 messages per hour during beta",
            "🎁 Free access during beta period",
            "👥 Early access to new features",
            "💬 Direct feedback channel to developers",
        ],
        "premium_features": [
            "🚀 60 messages per hour",
            "📈 Advanced analytics and insights",
            "🔗 API access for integrations",
            "🎯 Priority support",
        ],
        "upgrade_url": "/settings/subscription" if not has_access else None,
        "message": (
            "Upgrade to Premium to unlock Grapple AI Coach!"
            if not has_access
            else "You have access to Grapple AI Coach!"
        ),
    }


# ============================================================================
# Premium Endpoints (Beta, Premium, Admin only)
# ============================================================================

@router.post("/chat", response_model=ChatResponse)
@require_beta_or_premium
async def chat_with_grapple(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Send a message to Grapple AI Coach.

    Requires beta, premium, or admin subscription tier.

    This is a placeholder implementation. Full implementation will include:
    - Rate limiting check
    - Session management
    - LLM client call with failover
    - Token monitoring and cost tracking
    - Context building from user data
    """
    # TODO: Implement in Task 3
    # For now, return a placeholder response

    logger.info(f"Grapple chat request from user {current_user['id']}")

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Grapple chat endpoint is under construction. Coming soon!",
    )


@router.get("/sessions", response_model=SessionListResponse)
@require_beta_or_premium
async def get_chat_sessions(
    current_user: dict = Depends(get_current_user),
    limit: int = 20,
    offset: int = 0,
):
    """
    Get list of user's chat sessions with Grapple.

    Requires beta, premium, or admin subscription tier.
    """
    # TODO: Implement in Task 4

    logger.info(f"Fetching sessions for user {current_user['id']}")

    # Placeholder response
    return SessionListResponse(sessions=[])


@router.get("/sessions/{session_id}")
@require_beta_or_premium
async def get_chat_session(
    session_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Get a specific chat session with all messages.

    Requires beta, premium, or admin subscription tier.
    """
    # TODO: Implement in Task 4

    logger.info(f"Fetching session {session_id} for user {current_user['id']}")

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Session retrieval is under construction. Coming soon!",
    )


@router.delete("/sessions/{session_id}")
@require_beta_or_premium
async def delete_chat_session(
    session_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Delete a chat session.

    Requires beta, premium, or admin subscription tier.
    """
    # TODO: Implement in Task 4

    logger.info(f"Deleting session {session_id} for user {current_user['id']}")

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Session deletion is under construction. Coming soon!",
    )


@router.get("/usage")
@require_beta_or_premium
async def get_usage_stats(
    current_user: dict = Depends(get_current_user),
):
    """
    Get user's Grapple usage statistics.

    Returns:
        - Messages sent today/this week/this month
        - Tokens used
        - Cost incurred
        - Rate limit status
    """
    # TODO: Implement in Task 5

    logger.info(f"Fetching usage stats for user {current_user['id']}")

    # Placeholder response
    return {
        "user_id": current_user['id'],
        "tier": current_user.get('subscription_tier', 'free'),
        "usage": {
            "messages_today": 0,
            "messages_this_week": 0,
            "messages_this_month": 0,
            "tokens_used_total": 0,
            "cost_usd_total": 0.0,
        },
        "limits": {
            "messages_per_hour": 30 if current_user.get('subscription_tier') == 'beta' else 60,
            "monthly_cost_limit_usd": 5.0 if current_user.get('subscription_tier') == 'beta' else 50.0,
        },
        "rate_limit": {
            "current_window_messages": 0,
            "remaining_in_window": 30,
            "window_resets_at": datetime.utcnow().isoformat(),
        },
    }
