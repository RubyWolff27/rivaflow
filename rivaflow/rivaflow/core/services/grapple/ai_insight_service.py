"""Service for generating AI-powered training insights."""

import json
import logging

from rivaflow.core.services.grapple.llm_client import (
    GrappleLLMClient,
)
from rivaflow.core.services.insights_analytics import (
    InsightsAnalyticsService,
)
from rivaflow.db.repositories.ai_insight_repo import (
    AIInsightRepository,
)
from rivaflow.db.repositories.session_repo import (
    SessionRepository,
)

logger = logging.getLogger(__name__)

INSIGHT_SYSTEM_PROMPT = """\
You are Grapple, an elite BJJ coach with coral-belt-level expertise \
analysing training data. Generate a brief, actionable insight that \
demonstrates deep understanding of BJJ training principles — \
periodisation, technique selection, recovery science, and competition \
preparation. Reference specific positions, techniques, or training \
patterns rather than giving generic fitness advice.

Return JSON with:
{
  "title": "Short title (max 60 chars)",
  "content": "2-3 sentence insight with specific, actionable BJJ advice",
  "category": "observation|pattern|focus|recovery"
}

Only return valid JSON. No markdown fences."""


def _get_mode_context(user_id: int) -> str:
    """Get training mode context for insight generation."""
    try:
        from rivaflow.db.repositories.coach_preferences_repo import (
            CoachPreferencesRepository,
        )

        prefs = CoachPreferencesRepository.get(user_id)
        if not prefs:
            return ""
        mode = prefs.get("training_mode", "lifestyle")
        parts = []
        if mode == "competition_prep":
            comp = prefs.get("comp_name") or "upcoming competition"
            parts.append(f"Athlete is in competition prep for {comp}.")
        elif mode == "recovery":
            parts.append("Athlete is in recovery mode — prioritize safety.")
        elif mode == "skill_development":
            parts.append("Athlete is focused on skill development.")
        else:
            parts.append("Athlete trains for lifestyle and health.")
        injuries = prefs.get("injuries") or []
        if injuries:
            areas = [inj.get("area", "") for inj in injuries[:3] if inj.get("area")]
            if areas:
                parts.append(f"Injuries: {', '.join(areas)}.")
        return " ".join(parts)
    except Exception:
        return ""


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

    # Enrich with deep analytics
    try:
        insights_svc = InsightsAnalyticsService()
        load = insights_svc.get_training_load_management(user_id, days=90)
        context += f"ACWR: {load['current_acwr']} ({load['current_zone']}). "
        risk = insights_svc.get_overtraining_risk(user_id)
        context += f"Overtraining risk: {risk['risk_score']}/100 ({risk['level']}). "
        quality = insights_svc.get_session_quality_scores(user_id)
        context += f"Avg session quality: {quality['avg_quality']}/100. "
    except Exception:
        pass

    # Enrich with WHOOP recovery for session date
    try:
        from rivaflow.db.repositories.whoop_connection_repo import (
            WhoopConnectionRepository,
        )
        from rivaflow.db.repositories.whoop_recovery_cache_repo import (
            WhoopRecoveryCacheRepository,
        )
        from rivaflow.db.repositories.whoop_workout_cache_repo import (
            WhoopWorkoutCacheRepository,
        )

        conn = WhoopConnectionRepository.get_by_user_id(user_id)
        if conn and conn.get("is_active"):
            s_date = session.get("session_date", "")
            if s_date:
                d = str(s_date)
                recs = WhoopRecoveryCacheRepository.get_by_date_range(
                    user_id, d, d + "T23:59:59"
                )
                if recs:
                    rec = recs[-1]
                    rs = rec.get("recovery_score")
                    hv = rec.get("hrv_ms")
                    if rs is not None:
                        context += f"WHOOP Recovery: {rs:.0f}%"
                        if hv is not None:
                            context += f", HRV: {hv:.0f}ms"
                        wo = WhoopWorkoutCacheRepository.get_by_session_id(session_id)
                        if wo and wo.get("strain") is not None:
                            context += f", Session Strain: {wo['strain']}"
                        context += ". "
    except Exception:
        pass

    try:
        client = GrappleLLMClient(environment="production")
    except RuntimeError:
        logger.error("No LLM providers for insight gen")
        return None

    mode_ctx = _get_mode_context(user_id)
    user_content = f"{context}\n\n{session_summary}"
    if mode_ctx:
        user_content = f"{mode_ctx}\n\n{user_content}"

    messages = [
        {
            "role": "system",
            "content": INSIGHT_SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": user_content,
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

    # Enrich with WHOOP weekly averages
    whoop_line = ""
    try:
        from datetime import date as date_cls
        from datetime import timedelta

        from rivaflow.db.repositories.whoop_connection_repo import (
            WhoopConnectionRepository,
        )
        from rivaflow.db.repositories.whoop_recovery_cache_repo import (
            WhoopRecoveryCacheRepository,
        )

        conn = WhoopConnectionRepository.get_by_user_id(user_id)
        if conn and conn.get("is_active"):
            end_dt = date_cls.today().isoformat() + "T23:59:59"
            start_dt = (date_cls.today() - timedelta(days=7)).isoformat()
            recs = WhoopRecoveryCacheRepository.get_by_date_range(
                user_id, start_dt, end_dt
            )
            if recs:
                rec_vals = [
                    r["recovery_score"]
                    for r in recs
                    if r.get("recovery_score") is not None
                ]
                hrv_vals = [r["hrv_ms"] for r in recs if r.get("hrv_ms") is not None]
                sleep_vals = [
                    r["sleep_performance"]
                    for r in recs
                    if r.get("sleep_performance") is not None
                ]
                parts = []
                if rec_vals:
                    avg_r = sum(rec_vals) / len(rec_vals)
                    parts.append(f"avg recovery {avg_r:.0f}%")
                if hrv_vals:
                    avg_h = sum(hrv_vals) / len(hrv_vals)
                    parts.append(f"avg HRV {avg_h:.0f}ms")
                if sleep_vals:
                    avg_s = sum(sleep_vals) / len(sleep_vals)
                    parts.append(f"avg sleep {avg_s:.0f}%")
                if parts:
                    whoop_line = "WHOOP Weekly: " + ", ".join(parts)
    except Exception:
        pass

    try:
        client = GrappleLLMClient(environment="production")
    except RuntimeError:
        return None

    mode_ctx = _get_mode_context(user_id)
    weekly_content = ""
    if mode_ctx:
        weekly_content = mode_ctx + "\n\n"
    weekly_content += (
        "Generate a weekly training pattern "
        "insight from these recent sessions:\n" + "\n".join(summary_lines)
    )
    if whoop_line:
        weekly_content += "\n" + whoop_line

    messages = [
        {
            "role": "system",
            "content": INSIGHT_SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": weekly_content,
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
