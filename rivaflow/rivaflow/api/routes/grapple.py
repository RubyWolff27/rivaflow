"""Grapple AI Coach — chat endpoints (create session, send message, list/get/delete sessions)."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from rivaflow.core.dependencies import get_current_user
from rivaflow.core.error_handling import route_error_handler
from rivaflow.core.middleware.feature_access import require_beta_or_premium

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


# ============================================================================
# Chat Endpoints
# ============================================================================


@router.post("/chat", response_model=ChatResponse)
@require_beta_or_premium
@route_error_handler("chat_with_grapple", detail="Chat service error")
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
    except Exception:
        logger.exception(f"Unhandled error in grapple chat for user {user_id}")
        return JSONResponse(
            status_code=500,
            content={
                "detail": "An unexpected error occurred in chat",
            },
        )


async def _handle_chat(
    request: ChatRequest, user_id: int, user_tier: str
) -> ChatResponse:
    """Inner chat handler with step-by-step error reporting."""
    from rivaflow.core.services.chat_service import ChatService
    from rivaflow.core.services.grapple.context_builder import GrappleContextBuilder
    from rivaflow.core.services.grapple.llm_client import GrappleLLMClient
    from rivaflow.core.services.grapple.rate_limiter import GrappleRateLimiter
    from rivaflow.core.services.grapple.token_monitor import GrappleTokenMonitor

    # Step 1: Check rate limit
    try:
        rate_limiter = GrappleRateLimiter()
        rate_check = rate_limiter.check_rate_limit(user_id, user_tier)
    except (ConnectionError, OSError) as e:
        logger.critical(
            f"Rate limit service down for user {user_id}: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Rate limiting service unavailable. Please try again shortly.",
        )

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
        chat_service = ChatService()

        if request.session_id:
            session = chat_service.get_session_by_id(request.session_id, user_id)
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Session not found or access denied",
                )
        else:
            session = chat_service.create_session(user_id, title="New Chat")

        session_id = session["id"]
    except HTTPException:
        raise
    except (ConnectionError, OSError, KeyError) as e:
        logger.error(f"Session create/get failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to create chat session",
        )

    # Step 3: Store user message
    try:
        chat_service.create_message(
            session_id=session_id,
            role="user",
            content=request.message,
        )
    except (ConnectionError, OSError, KeyError) as e:
        logger.error(f"Failed to store user message: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to store message",
        )

    # Step 4: Build context
    try:
        context_builder = GrappleContextBuilder(user_id)
        recent_messages = chat_service.get_recent_context(session_id, max_messages=10)
        messages = context_builder.get_conversation_context(recent_messages)
    except (ConnectionError, OSError, KeyError) as e:
        logger.error(f"Context build failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to build context",
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
    except (ConnectionError, OSError, TimeoutError, RuntimeError) as e:
        logger.error(f"LLM call failed for user {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service is temporarily unavailable",
        )

    # Steps 6-9: Post-LLM bookkeeping (non-fatal — don't fail the response)
    try:
        assistant_message = chat_service.create_message(
            session_id=session_id,
            role="assistant",
            content=llm_response["content"],
            input_tokens=llm_response["input_tokens"],
            output_tokens=llm_response["output_tokens"],
            cost_usd=llm_response["cost_usd"],
        )
    except (ConnectionError, OSError) as e:
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
    except (ConnectionError, OSError) as e:
        logger.error(f"Failed to log token usage: {e}", exc_info=True)

    try:
        chat_service.update_session_stats(
            session_id=session_id,
            message_count_delta=2,
            tokens_delta=llm_response["total_tokens"],
            cost_delta=llm_response["cost_usd"],
        )
    except (ConnectionError, OSError) as e:
        logger.error(f"Failed to update session stats: {e}", exc_info=True)

    try:
        rate_limiter.record_message(user_id)
    except (ConnectionError, OSError) as e:
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
@route_error_handler("get_chat_sessions", detail="Failed to get chat sessions")
def get_chat_sessions(
    current_user: dict = Depends(get_current_user),
    limit: int = 20,
    offset: int = 0,
):
    """
    Get list of user's chat sessions with Grapple.

    Requires beta, premium, or admin subscription tier.
    """
    from rivaflow.core.services.chat_service import ChatService

    user_id = current_user["id"]
    logger.info(f"Fetching sessions for user {user_id}")

    chat_service = ChatService()
    sessions = chat_service.get_sessions_by_user(user_id, limit=limit, offset=offset)

    return SessionListResponse(sessions=sessions)


@router.get("/sessions/{session_id}")
@require_beta_or_premium
@route_error_handler("get_chat_session", detail="Failed to get chat session")
def get_chat_session(
    session_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Get a specific chat session with all messages.

    Requires beta, premium, or admin subscription tier.
    """
    from rivaflow.core.services.chat_service import ChatService

    user_id = current_user["id"]
    logger.info(f"Fetching session {session_id} for user {user_id}")

    chat_service = ChatService()

    # Get session (includes ownership check)
    session = chat_service.get_session_by_id(session_id, user_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or access denied",
        )

    # Get messages
    messages = chat_service.get_messages_by_session(session_id)

    return {
        "session": session,
        "messages": messages,
    }


@router.delete("/sessions/{session_id}")
@require_beta_or_premium
@route_error_handler("delete_chat_session", detail="Failed to delete chat session")
def delete_chat_session(
    session_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Delete a chat session.

    Requires beta, premium, or admin subscription tier.
    """
    from rivaflow.core.services.chat_service import ChatService

    user_id = current_user["id"]
    logger.info(f"Deleting session {session_id} for user {user_id}")

    chat_service = ChatService()
    deleted = chat_service.delete_session(session_id, user_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or access denied",
        )

    return {"message": "Session deleted"}
