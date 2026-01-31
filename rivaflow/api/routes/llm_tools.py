"""
LLM tool contract endpoints - skeletons for future AI features.

BETA STATUS: These endpoints return placeholder data and are not used in the UI.
Planned for v0.2+ for AI-powered training insights and recommendations.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from datetime import date
from typing import List, Dict, Any

from rivaflow.core.dependencies import get_current_user

router = APIRouter(prefix="/llm-tools", tags=["llm-tools"])


class WeekReportResponse(BaseModel):
    """Week report response for LLM consumption."""
    summary: str
    sessions: List[Dict[str, Any]]


class PartnersSummaryResponse(BaseModel):
    """Partners summary response for LLM consumption."""
    partners: List[Dict[str, Any]]


@router.get("/report/week", response_model=WeekReportResponse)
async def get_week_report_for_llm(
    week_start: date,
    current_user: dict = Depends(get_current_user)
):
    """
    Get week report formatted for LLM tool calling.

    Args:
        week_start: Start date of the week (YYYY-MM-DD)
        current_user: Authenticated user

    Returns:
        Summary text and list of sessions for the week

    Status: STUB - Returns mock data. To be implemented with:
        - ReportService integration
        - PrivacyService.redact_for_llm() for session data
        - Natural language summary generation
    """
    # TODO: Implement with actual report generation
    return WeekReportResponse(
        summary=f"Week starting {week_start}: This is a placeholder summary. Implement with ReportService.",
        sessions=[
            {
                "date": str(week_start),
                "type": "training",
                "summary": "Example session - to be populated from database"
            }
        ]
    )


@router.get("/partners/summary", response_model=PartnersSummaryResponse)
async def get_partners_summary_for_llm(
    start: date,
    end: date,
    current_user: dict = Depends(get_current_user)
):
    """
    Get training partners summary for date range, formatted for LLM.

    Args:
        start: Start date (YYYY-MM-DD)
        end: End date (YYYY-MM-DD)
        current_user: Authenticated user

    Returns:
        List of training partners with aggregated stats

    Status: STUB - Returns mock data. To be implemented with:
        - ContactsRepository integration
        - Session partner relationship queries
        - Aggregated training statistics per partner
    """
    # TODO: Implement with actual partner statistics
    return PartnersSummaryResponse(
        partners=[
            {
                "name": "Example Partner",
                "sessions_count": 0,
                "note": "Placeholder - to be populated from contacts and sessions"
            }
        ]
    )
