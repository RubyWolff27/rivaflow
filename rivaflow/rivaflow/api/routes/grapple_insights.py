"""Grapple AI Coach — insight generation, history, and feedback endpoints."""

import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from rivaflow.core.dependencies import get_current_user
from rivaflow.core.error_handling import route_error_handler
from rivaflow.core.exceptions import (
    ExternalServiceError,
    NotFoundError,
    RivaFlowException,
    ValidationError,
)
from rivaflow.core.middleware.feature_access import require_beta_or_premium

router = APIRouter(tags=["grapple"])
logger = logging.getLogger(__name__)


# ============================================================================
# Request/Response Models
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
# Insight / Extraction Endpoints
# ============================================================================


@router.post("/extract-session")
@require_beta_or_premium
@route_error_handler("extract_session", detail="Failed to extract session")
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
        logger.error("Session extraction failed: %s", e)
        raise ExternalServiceError(
            "Session extraction service is temporarily unavailable"
        )


@router.post("/save-extracted-session")
@require_beta_or_premium
@route_error_handler("save_extracted_session", detail="Failed to save session")
def save_extracted_session(
    request: SaveExtractedSessionRequest,
    current_user: dict = Depends(get_current_user),
):
    """Save a previously extracted session."""
    from datetime import date

    from rivaflow.core.services.session_service import SessionService
    from rivaflow.db.repositories.session_event_repo import (
        SessionEventRepository,
    )

    user_id = current_user["id"]

    session_service = SessionService()
    session_id = session_service.create_session(
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
@route_error_handler("list_insights", detail="Failed to list insights")
def list_insights(
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
@route_error_handler("generate_insight", detail="Failed to generate insight")
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
        raise ValidationError("Invalid insight_type or missing session_id")

    if not insight:
        raise NotFoundError("Could not generate insight")

    return insight


@router.post("/insights/{insight_id}/chat")
@require_beta_or_premium
@route_error_handler("create_insight_chat", detail="Failed to create insight chat")
async def create_insight_chat(
    insight_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Create a chat session seeded with an insight's content."""
    user_id = current_user["id"]

    try:
        return await _handle_insight_chat(insight_id, user_id)
    except (HTTPException, RivaFlowException):
        raise
    except Exception:
        logger.exception("Unhandled error in insight chat for user %s", user_id)
        return JSONResponse(
            status_code=500,
            content={
                "detail": "An unexpected error occurred in chat",
            },
        )


def _insight_chat_sync(insight_id: int, user_id: int) -> dict:
    """Sync DB work for creating an insight-seeded chat session.

    Returns a dict with the chat_session_id and insight data.
    """
    from rivaflow.core.services.chat_service import ChatService
    from rivaflow.db.repositories.ai_insight_repo import AIInsightRepository

    insight = AIInsightRepository.get_by_id(insight_id, user_id)
    if not insight:
        raise NotFoundError("Insight not found")

    chat_service = ChatService()

    # If already has a chat session, return it (idempotent)
    existing_id = (insight.get("data") or {}).get("chat_session_id")
    if existing_id:
        existing = chat_service.get_session_by_id(existing_id, user_id)
        if existing:
            return {"chat_session_id": existing_id, "insight": insight}

    # Create new chat session seeded with the insight
    title = f"Insight: {insight['title']}"
    session = chat_service.create_session(user_id, title=title)
    session_id = session["id"]

    seed_content = f"**{insight['title']}**\n\n{insight['content']}"
    chat_service.create_message(
        session_id=session_id,
        role="assistant",
        content=seed_content,
    )
    chat_service.update_session_stats(
        session_id=session_id,
        message_count_delta=1,
    )

    # Store chat_session_id in insight data
    data = insight.get("data") or {}
    data["chat_session_id"] = session_id
    AIInsightRepository.update_data(insight_id, user_id, data)

    # Mark insight as read
    AIInsightRepository.mark_as_read(insight_id, user_id)

    return {"chat_session_id": session_id, "insight": insight}


async def _handle_insight_chat(insight_id: int, user_id: int):
    """Inner handler for insight chat creation — runs sync DB work off the event loop."""
    return await asyncio.to_thread(_insight_chat_sync, insight_id, user_id)


@router.post("/technique-qa")
@require_beta_or_premium
@route_error_handler("technique_qa", detail="Failed to process technique Q&A")
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
        logger.error("Technique QA failed: %s", e)
        raise ExternalServiceError("Technique QA service is temporarily unavailable")
