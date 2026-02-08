"""
LLM tool contract endpoints - skeletons for future AI features.

BETA STATUS: These endpoints return placeholder data and are not used in the UI.
Planned for v0.2+ for AI-powered training insights and recommendations.
"""

from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address

from rivaflow.core.dependencies import get_current_user

router = APIRouter(prefix="/llm-tools", tags=["llm-tools"])
limiter = Limiter(key_func=get_remote_address)


class WeekReportResponse(BaseModel):
    """Week report response for LLM consumption."""

    summary: str
    sessions: list[dict[str, Any]]


class PartnersSummaryResponse(BaseModel):
    """Partners summary response for LLM consumption."""

    partners: list[dict[str, Any]]


@router.get("/report/week", response_model=WeekReportResponse)
@limiter.limit("20/minute")
def get_week_report_for_llm(
    request: Request, week_start: date, current_user: dict = Depends(get_current_user)
):
    """
    Get week report formatted for LLM tool calling.

    Args:
        week_start: Start date of the week (YYYY-MM-DD)
        current_user: Authenticated user

    Returns:
        Summary text and list of sessions for the week

    Status: PLACEHOLDER - Returns mock data for API contract definition.

    PLANNED FOR v0.4+: Will be implemented with:
        - ReportService integration for actual data
        - PrivacyService.redact_for_llm() for session data
        - Natural language summary generation
        - LLM-powered training insights
    """
    # PLACEHOLDER: Returns mock data - not used in beta
    return WeekReportResponse(
        summary=f"Week starting {week_start}: This is a placeholder summary. Implement with ReportService.",
        sessions=[
            {
                "date": str(week_start),
                "type": "training",
                "summary": "Example session - to be populated from database",
            }
        ],
    )


@router.get("/partners/summary", response_model=PartnersSummaryResponse)
@limiter.limit("20/minute")
def get_partners_summary_for_llm(
    request: Request,
    start: date,
    end: date,
    current_user: dict = Depends(get_current_user),
):
    """
    Get training partners summary for date range, formatted for LLM.

    Args:
        start: Start date (YYYY-MM-DD)
        end: End date (YYYY-MM-DD)
        current_user: Authenticated user

    Returns:
        List of training partners with aggregated stats

    Status: PLACEHOLDER - Returns mock data for API contract definition.

    PLANNED FOR v0.4+: Will be implemented with:
        - FriendRepository integration
        - Session partner relationship queries
        - Aggregated training statistics per partner
        - LLM-powered partner insights
    """
    # PLACEHOLDER: Returns mock data - not used in beta
    return PartnersSummaryResponse(
        partners=[
            {
                "name": "Example Partner",
                "sessions_count": 0,
                "note": "Placeholder - to be populated from contacts and sessions",
            }
        ]
    )
