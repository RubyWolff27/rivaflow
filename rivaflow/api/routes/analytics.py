"""Analytics and dashboard endpoints."""
from fastapi import APIRouter, Query, Depends
from datetime import date
from typing import Optional

from rivaflow.core.services.analytics_service import AnalyticsService
from rivaflow.core.dependencies import get_current_user
from rivaflow.core.exceptions import ValidationError, NotFoundError

router = APIRouter()
service = AnalyticsService()


@router.get("/performance-overview")
async def get_performance_overview(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    """Get performance overview dashboard data."""
    return service.get_performance_overview(user_id=current_user["id"], start_date=start_date, end_date=end_date)


@router.get("/partners/stats")
async def get_partner_analytics(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    """Get partner analytics dashboard data."""
    return service.get_partner_analytics(user_id=current_user["id"], start_date=start_date, end_date=end_date)


@router.get("/partners/head-to-head")
async def get_head_to_head(
    partner1_id: int = Query(...),
    partner2_id: int = Query(...),
    current_user: dict = Depends(get_current_user),
):
    """Get head-to-head comparison between two partners."""
    try:
        result = service.get_head_to_head(user_id=current_user["id"], partner1_id=partner1_id, partner2_id=partner2_id)
        if not result:
            raise NotFoundError("One or both partners not found")
        return result
    except HTTPException:
        raise


@router.get("/readiness/trends")
async def get_readiness_trends(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    """Get readiness and recovery analytics."""
    return service.get_readiness_trends(user_id=current_user["id"], start_date=start_date, end_date=end_date)


@router.get("/whoop/analytics")
async def get_whoop_analytics(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    """Get Whoop fitness tracker analytics."""
    return service.get_whoop_analytics(user_id=current_user["id"], start_date=start_date, end_date=end_date)


@router.get("/techniques/breakdown")
async def get_technique_analytics(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    """Get technique mastery analytics."""
    return service.get_technique_analytics(user_id=current_user["id"], start_date=start_date, end_date=end_date)


@router.get("/consistency/metrics")
async def get_consistency_analytics(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    """Get training consistency analytics."""
    return service.get_consistency_analytics(user_id=current_user["id"], start_date=start_date, end_date=end_date)


@router.get("/milestones")
async def get_milestones(current_user: dict = Depends(get_current_user)):
    """Get progression and milestone data."""
    return service.get_milestones(user_id=current_user["id"])


@router.get("/instructors/insights")
async def get_instructor_analytics(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    """Get instructor insights analytics."""
    return service.get_instructor_analytics(user_id=current_user["id"], start_date=start_date, end_date=end_date)
