"""Grapple AI Coach API routes - Premium BJJ coaching with cloud LLMs."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from rivaflow.core.dependencies import get_current_user
from rivaflow.core.middleware.feature_access import (
    get_user_tier_info,
    require_beta_or_premium,
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
    session_id: str | None = None  # If None, creates new session


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

    sessions: list[dict]


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
    tier = current_user.get("subscription_tier", "free")
    has_access = tier in ["beta", "premium", "admin"]

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

    Flow:
    1. Check rate limit
    2. Create or get session
    3. Build context from user training data
    4. Call LLM with failover
    5. Log token usage
    6. Store messages
    7. Update session stats
    """
    user_id = current_user["id"]
    user_tier = current_user.get("subscription_tier", "free")

    logger.info(f"Grapple chat request from user {user_id} (tier: {user_tier})")

    # Top-level try/except ensures we ALWAYS return a proper JSON response
    # (never an unhandled exception that strips CORS headers)
    try:
        return await _handle_chat(request, user_id, user_tier)
    except HTTPException:
        raise  # Let FastAPI handle these normally (they keep CORS headers)
    except Exception as e:
        logger.exception(f"Unhandled error in grapple chat for user {user_id}")
        return JSONResponse(
            status_code=500,
            content={
                "detail": f"Chat error: {type(e).__name__}: {str(e)}",
            },
        )


async def _handle_chat(
    request: ChatRequest, user_id: int, user_tier: str
) -> ChatResponse:
    """Inner chat handler with step-by-step error reporting."""
    from rivaflow.core.services.grapple.context_builder import GrappleContextBuilder
    from rivaflow.core.services.grapple.llm_client import GrappleLLMClient
    from rivaflow.core.services.grapple.rate_limiter import GrappleRateLimiter
    from rivaflow.core.services.grapple.token_monitor import GrappleTokenMonitor
    from rivaflow.db.repositories.chat_message_repo import ChatMessageRepository
    from rivaflow.db.repositories.chat_session_repo import ChatSessionRepository

    # Step 1: Check rate limit
    try:
        rate_limiter = GrappleRateLimiter()
        rate_check = rate_limiter.check_rate_limit(user_id, user_tier)
    except Exception as e:
        logger.error(f"Rate limit check failed for user {user_id}: {e}", exc_info=True)
        # Fail open — allow the request if rate limiting is broken
        rate_check = {"allowed": True, "remaining": 99, "limit": 99}

    if not rate_check["allowed"]:
        reset_at = rate_check.get("reset_at")
        reset_str = (
            reset_at.isoformat() if hasattr(reset_at, "isoformat") else str(reset_at)
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "rate_limit_exceeded",
                "message": rate_check["reason"],
                "limit": rate_check["limit"],
                "remaining": rate_check["remaining"],
                "reset_at": reset_str,
            },
        )

    # Step 2: Get or create session
    try:
        session_repo = ChatSessionRepository()
        message_repo = ChatMessageRepository()

        if request.session_id:
            session = session_repo.get_by_id(request.session_id, user_id)
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Session not found or access denied",
                )
        else:
            session = session_repo.create(user_id, title="New Chat")

        session_id = session["id"]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Session create/get failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create chat session: {type(e).__name__}: {e}",
        )

    # Step 3: Store user message
    try:
        message_repo.create(
            session_id=session_id,
            role="user",
            content=request.message,
        )
    except Exception as e:
        logger.error(f"Failed to store user message: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to store message: {type(e).__name__}: {e}",
        )

    # Step 4: Build context
    try:
        context_builder = GrappleContextBuilder(user_id)
        recent_messages = message_repo.get_recent_context(session_id, max_messages=10)
        messages = context_builder.get_conversation_context(recent_messages)
    except Exception as e:
        logger.error(f"Context build failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to build context: {type(e).__name__}: {e}",
        )

    # Step 5: Call LLM
    try:
        llm_client = GrappleLLMClient(environment="production")
        llm_response = await llm_client.chat(
            messages=messages,
            user_id=user_id,
            temperature=0.7,
            max_tokens=1024,
        )
    except Exception as e:
        logger.error(f"LLM call failed for user {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI service unavailable: {type(e).__name__}: {e}",
        )

    # Steps 6-9: Post-LLM bookkeeping (non-fatal — don't fail the response)
    try:
        assistant_message = message_repo.create(
            session_id=session_id,
            role="assistant",
            content=llm_response["content"],
            input_tokens=llm_response["input_tokens"],
            output_tokens=llm_response["output_tokens"],
            cost_usd=llm_response["cost_usd"],
        )
    except Exception as e:
        logger.error(f"Failed to store assistant message: {e}", exc_info=True)
        assistant_message = {"id": "unknown"}

    try:
        token_monitor = GrappleTokenMonitor()
        token_monitor.log_usage(
            user_id=user_id,
            session_id=session_id,
            message_id=assistant_message["id"],
            provider=llm_response["provider"],
            model=llm_response["model"],
            input_tokens=llm_response["input_tokens"],
            output_tokens=llm_response["output_tokens"],
            cost_usd=llm_response["cost_usd"],
        )
    except Exception as e:
        logger.error(f"Failed to log token usage: {e}", exc_info=True)

    try:
        session_repo.update_stats(
            session_id=session_id,
            message_count_delta=2,
            tokens_delta=llm_response["total_tokens"],
            cost_delta=llm_response["cost_usd"],
        )
    except Exception as e:
        logger.error(f"Failed to update session stats: {e}", exc_info=True)

    try:
        rate_limiter.record_message(user_id)
    except Exception as e:
        logger.error(f"Failed to record rate limit: {e}", exc_info=True)

    # Step 10: Return response
    logger.info(
        f"Grapple response for user {user_id}: "
        f"{llm_response['total_tokens']} tokens, "
        f"${llm_response['cost_usd']:.6f} via {llm_response['provider']}"
    )

    return ChatResponse(
        session_id=session_id,
        message_id=assistant_message["id"],
        reply=llm_response["content"],
        tokens_used=llm_response["total_tokens"],
        cost_usd=llm_response["cost_usd"],
        rate_limit_remaining=max(0, rate_check.get("remaining", 1) - 1),
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
    from rivaflow.db.repositories.chat_session_repo import ChatSessionRepository

    user_id = current_user["id"]
    logger.info(f"Fetching sessions for user {user_id}")

    session_repo = ChatSessionRepository()
    sessions = session_repo.get_by_user(user_id, limit=limit, offset=offset)

    return SessionListResponse(sessions=sessions)


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
    from rivaflow.db.repositories.chat_message_repo import ChatMessageRepository
    from rivaflow.db.repositories.chat_session_repo import ChatSessionRepository

    user_id = current_user["id"]
    logger.info(f"Fetching session {session_id} for user {user_id}")

    session_repo = ChatSessionRepository()
    message_repo = ChatMessageRepository()

    # Get session (includes ownership check)
    session = session_repo.get_by_id(session_id, user_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or access denied",
        )

    # Get messages
    messages = message_repo.get_by_session(session_id)

    return {
        "session": session,
        "messages": messages,
    }


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
    from rivaflow.db.repositories.chat_session_repo import ChatSessionRepository

    user_id = current_user["id"]
    logger.info(f"Deleting session {session_id} for user {user_id}")

    session_repo = ChatSessionRepository()
    deleted = session_repo.delete(session_id, user_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or access denied",
        )

    return {"success": True, "message": "Session deleted"}


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
        - Cost projections
    """
    from rivaflow.core.middleware.feature_access import FeatureAccess
    from rivaflow.core.services.grapple.rate_limiter import GrappleRateLimiter
    from rivaflow.core.services.grapple.token_monitor import GrappleTokenMonitor

    user_id = current_user["id"]
    user_tier = current_user.get("subscription_tier", "free")

    logger.info(f"Fetching usage stats for user {user_id}")

    # Get token usage stats
    token_monitor = GrappleTokenMonitor()
    usage_30d = token_monitor.get_user_usage(user_id)
    cost_projection = token_monitor.get_cost_projection(user_id)
    cost_limit_check = token_monitor.check_cost_limit(user_id, user_tier)

    # Get rate limit stats
    rate_limiter = GrappleRateLimiter()
    rate_stats = rate_limiter.get_user_usage_stats(user_id, days=7)
    rate_check = rate_limiter.check_rate_limit(user_id, user_tier)

    return {
        "user_id": user_id,
        "tier": user_tier,
        "usage_30_days": usage_30d,
        "cost_projection": cost_projection,
        "cost_limit": cost_limit_check,
        "rate_limit": {
            "current_status": {
                "allowed": rate_check["allowed"],
                "remaining": rate_check["remaining"],
                "limit": rate_check["limit"],
                "reset_at": rate_check["reset_at"].isoformat(),
            },
            "weekly_stats": rate_stats,
        },
        "limits": {
            "messages_per_hour": FeatureAccess.get_rate_limit(user_tier),
            "monthly_cost_limit_usd": FeatureAccess.get_cost_limit(user_tier),
        },
    }


# ============================================================================
# Request/Response Models for Enhanced Grapple
# ============================================================================


class ExtractSessionRequest(BaseModel):
    """Request to extract session data from text."""

    text: str


class SaveExtractedSessionRequest(BaseModel):
    """Confirm and save an extracted session."""

    session_date: str
    class_type: str = "gi"
    gym_name: str = ""
    duration_mins: int = 60
    intensity: int = 3
    rolls: int = 0
    submissions_for: int = 0
    submissions_against: int = 0
    partners: list[str] = []
    techniques: list[str] = []
    notes: str = ""
    events: list[dict] = []


class GenerateInsightRequest(BaseModel):
    """Request to generate an AI insight."""

    insight_type: str = "post_session"
    session_id: int | None = None


class TechniqueQARequest(BaseModel):
    """Request for technique Q&A."""

    question: str


# ============================================================================
# Enhanced Grapple Endpoints
# ============================================================================


@router.post("/extract-session")
@require_beta_or_premium
async def extract_session(
    request: ExtractSessionRequest,
    current_user: dict = Depends(get_current_user),
):
    """Parse natural language into structured session data."""
    from rivaflow.core.services.grapple.session_extraction_service import (
        extract_session_from_text,
    )

    user_id = current_user["id"]
    try:
        result = await extract_session_from_text(request.text, user_id)
        return result
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )


@router.post("/save-extracted-session")
@require_beta_or_premium
async def save_extracted_session(
    request: SaveExtractedSessionRequest,
    current_user: dict = Depends(get_current_user),
):
    """Save a previously extracted session."""
    from datetime import date

    from rivaflow.db.repositories.session_event_repo import (
        SessionEventRepository,
    )
    from rivaflow.db.repositories.session_repo import (
        SessionRepository,
    )

    user_id = current_user["id"]

    session_id = SessionRepository.create(
        user_id=user_id,
        session_date=date.fromisoformat(request.session_date),
        class_type=request.class_type,
        gym_name=request.gym_name,
        duration_mins=request.duration_mins,
        intensity=request.intensity,
        rolls=request.rolls,
        submissions_for=request.submissions_for,
        submissions_against=request.submissions_against,
        partners=request.partners,
        techniques=request.techniques,
        notes=request.notes,
    )

    # Save events if present
    if request.events:
        events = []
        for i, evt in enumerate(request.events):
            events.append(
                {
                    "session_id": session_id,
                    "user_id": user_id,
                    "event_type": evt.get("event_type", "technique"),
                    "technique_name": evt.get("technique_name"),
                    "position": evt.get("position"),
                    "outcome": evt.get("outcome"),
                    "partner_name": evt.get("partner_name"),
                    "event_order": i,
                }
            )
        SessionEventRepository.bulk_create(events)

    return {
        "session_id": session_id,
        "message": "Session saved successfully",
    }


@router.get("/insights")
@require_beta_or_premium
async def list_insights(
    current_user: dict = Depends(get_current_user),
    limit: int = 20,
    insight_type: str | None = None,
):
    """List user's AI insights."""
    from rivaflow.db.repositories.ai_insight_repo import (
        AIInsightRepository,
    )

    user_id = current_user["id"]
    insights = AIInsightRepository.list_by_user(
        user_id, limit=limit, insight_type=insight_type
    )
    return {
        "insights": insights,
        "count": len(insights),
    }


@router.post("/insights/generate")
@require_beta_or_premium
async def generate_insight(
    request: GenerateInsightRequest,
    current_user: dict = Depends(get_current_user),
):
    """Generate a new AI insight."""
    from rivaflow.core.services.grapple.ai_insight_service import (
        generate_post_session_insight,
        generate_weekly_insight,
    )

    user_id = current_user["id"]

    if request.insight_type == "post_session" and request.session_id:
        insight = await generate_post_session_insight(user_id, request.session_id)
    elif request.insight_type == "weekly":
        insight = await generate_weekly_insight(user_id)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=("Invalid insight_type or missing" " session_id"),
        )

    if not insight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Could not generate insight",
        )

    return insight


@router.post("/technique-qa")
@require_beta_or_premium
async def technique_qa_endpoint(
    request: TechniqueQARequest,
    current_user: dict = Depends(get_current_user),
):
    """Glossary-grounded technique Q&A."""
    from rivaflow.core.services.grapple.glossary_rag_service import (
        technique_qa,
    )

    user_id = current_user["id"]
    try:
        result = await technique_qa(request.question, user_id)
        return result
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
