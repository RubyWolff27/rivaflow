"""Chat API routes - proxy to Ollama LLM with BJJ coaching context."""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import httpx
from typing import List
from datetime import datetime, timedelta

from rivaflow.core.dependencies import get_current_user
from rivaflow.db.repositories.session_repo import SessionRepository
from rivaflow.db.repositories.user_repo import UserRepository
from rivaflow.core.services.privacy_service import PrivacyService

router = APIRouter(prefix="/chat", tags=["chat"])

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "llama3.1:8b"
TIMEOUT = 60.0


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[Message]


class ChatResponse(BaseModel):
    reply: str


def build_user_context(user_id: int) -> str:
    """Build context about user's training history for the LLM."""
    session_repo = SessionRepository()
    user_repo = UserRepository()

    # Get user profile
    user = user_repo.get_by_id(user_id)
    if not user:
        return "User profile not found."

    # Get recent sessions
    thirty_days_ago = (datetime.now() - timedelta(days=30)).date()
    sessions = session_repo.get_recent(user_id, limit=50)

    # Filter to last 30 days and redact for LLM
    recent_sessions = []
    for session in sessions:
        # session_date is a date object from _row_to_dict
        session_date = session["session_date"]
        if session_date >= thirty_days_ago:
            redacted = PrivacyService.redact_for_llm(session, include_notes=True)
            recent_sessions.append(redacted)

    # Build context string
    context_parts = [
        f"USER PROFILE:",
        f"Name: {user['first_name']} {user['last_name']}",
        f"Email: {user['email']}",
        f"",
        f"RECENT TRAINING (Last 30 days): {len(recent_sessions)} sessions",
    ]

    if recent_sessions:
        context_parts.append("")
        for session in recent_sessions[-10:]:  # Show last 10 sessions
            date_val = session.get("date", "Unknown")
            # Convert date object to string if needed
            date_str = str(date_val) if date_val != "Unknown" else "Unknown"
            gym = session.get("gym", "Unknown")
            duration = session.get("duration_mins", 0)
            intensity = session.get("intensity", 0)
            rolls = session.get("rolls_count", 0)
            techniques = session.get("techniques", [])
            notes = session.get("notes", "")

            session_summary = f"- {date_str} at {gym}: {duration}min, intensity {intensity}/10"
            if rolls > 0:
                session_summary += f", {rolls} rolls"
            if techniques:
                session_summary += f", techniques: {', '.join(techniques[:3])}"
            if notes:
                session_summary += f" | Notes: {notes[:100]}"

            context_parts.append(session_summary)
    else:
        context_parts.append("No recent training sessions logged.")

    return "\n".join(context_parts)


def build_system_prompt(user_context: str) -> str:
    """Build the system prompt with user context."""
    return f"""You are a knowledgeable Brazilian Jiu-Jitsu (BJJ) coach and health advisor for RivaFlow, a training management platform.

Your role is to:
1. Provide expert advice on BJJ technique, strategy, and training
2. Analyze the user's training patterns and provide personalized insights
3. Give recommendations on recovery, injury prevention, and training frequency
4. Help set realistic goals and track progress
5. Explain BJJ concepts, positions, and techniques clearly
6. Be supportive, motivating, and safety-conscious

Guidelines:
- Always prioritize safety and proper technique over ego or intensity
- Consider training frequency, intensity, and recovery in your advice
- Reference specific sessions when giving feedback
- Be concise but thorough
- If medical advice is needed, recommend seeing a doctor
- Use BJJ terminology appropriately but explain when needed

CURRENT USER DATA:
{user_context}

Now respond to the user's questions using this context. Reference their specific training data when relevant."""


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest, current_user: dict = Depends(get_current_user)):
    """
    Chat endpoint with BJJ coaching context.

    Args:
        request: Chat messages from user
        current_user: Authenticated user

    Returns:
        Assistant reply with personalized BJJ coaching
    """
    try:
        # Build user context and system prompt
        user_context = build_user_context(current_user["id"])
        system_prompt = build_system_prompt(user_context)

        # Prepend system message to conversation
        messages = [
            {"role": "system", "content": system_prompt}
        ] + [msg.model_dump() for msg in request.messages]

        # Call Ollama with full context
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(
                OLLAMA_URL,
                json={
                    "model": MODEL_NAME,
                    "messages": messages,
                    "stream": False,
                },
            )
            response.raise_for_status()
            data = response.json()
            return ChatResponse(reply=data["message"]["content"])

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="LLM request timed out")
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"LLM service error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")
