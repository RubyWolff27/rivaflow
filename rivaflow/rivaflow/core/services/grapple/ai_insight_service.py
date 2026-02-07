"""Service for generating AI-powered training insights."""

import json
import logging

from rivaflow.core.services.grapple.llm_client import (
    GrappleLLMClient,
)
from rivaflow.db.repositories.ai_insight_repo import (
    AIInsightRepository,
)
from rivaflow.db.repositories.session_repo import (
    SessionRepository,
)

logger = logging.getLogger(__name__)

INSIGHT_SYSTEM_PROMPT = """\
You are a BJJ coach analyzing training data. \
Generate a brief, actionable insight.

Return JSON with:
{
  "title": "Short title (max 60 chars)",
  "content": "2-3 sentence insight with specific advice",
  "category": "observation|pattern|focus|recovery"
}

Only return valid JSON. No markdown fences."""


async def generate_post_session_insight(user_id: int, session_id: int) -> dict | None:
    """Generate an insight after a training session.

    Args:
        user_id: User ID
        session_id: Session ID to analyze

    Returns:
        Created insight dict or None
    """
    session = SessionRepository.get_by_id(user_id, session_id)
    if not session:
        return None

    recent = SessionRepository.get_recent(user_id, limit=5)

    session_summary = (
        f"Latest session: {session.get('class_type', 'BJJ')} "
        f"at {session.get('gym_name', 'gym')}, "
        f"{session.get('duration_mins', 60)} min, "
        f"intensity {session.get('intensity', 3)}/5, "
        f"{session.get('rolls', 0)} rolls, "
        f"subs for: {session.get('submissions_for', 0)}, "
        f"subs against: "
        f"{session.get('submissions_against', 0)}"
    )
    if session.get("notes"):
        session_summary += f". Notes: {session['notes']}"

    context = f"Recent sessions: {len(recent)} in last period. "
    if recent:
        avg_intensity = sum(s.get("intensity", 3) for s in recent) / len(recent)
        context += f"Avg intensity: {avg_intensity:.1f}/5. "

    try:
        client = GrappleLLMClient(environment="production")
    except RuntimeError:
        logger.error("No LLM providers for insight gen")
        return None

    messages = [
        {
            "role": "system",
            "content": INSIGHT_SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": f"{context}\n\n{session_summary}",
        },
    ]

    try:
        result = await client.chat(
            messages=messages,
            user_id=user_id,
            temperature=0.7,
            max_tokens=256,
        )
    except (ConnectionError, OSError, TimeoutError, RuntimeError) as e:
        logger.error(f"Insight generation failed: {e}")
        return None

    content = result["content"].strip()
    if content.startswith("```"):
        lines = content.split("\n")
        lines = [ln for ln in lines if not ln.strip().startswith("```")]
        content = "\n".join(lines)

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        logger.warning("Failed to parse insight response")
        parsed = {
            "title": "Training Insight",
            "content": content[:500],
            "category": "observation",
        }

    insight_id = AIInsightRepository.create(
        user_id=user_id,
        session_id=session_id,
        insight_type="post_session",
        title=parsed.get("title", "Training Insight"),
        content=parsed.get("content", ""),
        category=parsed.get("category", "observation"),
        data={
            "llm_tokens": result.get("total_tokens", 0),
            "llm_cost": result.get("cost_usd", 0.0),
        },
    )

    return AIInsightRepository.get_by_id(insight_id, user_id)


async def generate_weekly_insight(
    user_id: int,
) -> dict | None:
    """Generate a weekly training insight."""
    recent = SessionRepository.get_recent(user_id, limit=10)
    if not recent:
        return None

    summary_lines = []
    for s in recent[:7]:
        line = (
            f"- {s.get('session_date')}: "
            f"{s.get('class_type', 'BJJ')}, "
            f"{s.get('duration_mins', 60)}min, "
            f"intensity {s.get('intensity', 3)}/5"
        )
        summary_lines.append(line)

    try:
        client = GrappleLLMClient(environment="production")
    except RuntimeError:
        return None

    messages = [
        {
            "role": "system",
            "content": INSIGHT_SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": (
                "Generate a weekly training pattern "
                "insight from these recent sessions:\n" + "\n".join(summary_lines)
            ),
        },
    ]

    try:
        result = await client.chat(
            messages=messages,
            user_id=user_id,
            temperature=0.7,
            max_tokens=256,
        )
    except (ConnectionError, OSError, TimeoutError, RuntimeError) as e:
        logger.error(f"Weekly insight failed: {e}")
        return None

    content = result["content"].strip()
    if content.startswith("```"):
        lines = content.split("\n")
        lines = [ln for ln in lines if not ln.strip().startswith("```")]
        content = "\n".join(lines)

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        parsed = {
            "title": "Weekly Training Insight",
            "content": content[:500],
            "category": "pattern",
        }

    insight_id = AIInsightRepository.create(
        user_id=user_id,
        insight_type="weekly",
        title=parsed.get("title", "Weekly Training Insight"),
        content=parsed.get("content", ""),
        category=parsed.get("category", "pattern"),
        data={
            "llm_tokens": result.get("total_tokens", 0),
            "sessions_analyzed": len(recent),
        },
    )

    return AIInsightRepository.get_by_id(insight_id, user_id)
