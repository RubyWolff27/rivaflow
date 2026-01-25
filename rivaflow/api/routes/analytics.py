"""Analytics and dashboard endpoints."""
from fastapi import APIRouter, HTTPException, Query
from datetime import date
from typing import Optional

from rivaflow.core.services.analytics_service import AnalyticsService

router = APIRouter()
service = AnalyticsService()


@router.get("/performance-overview")
async def get_performance_overview(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
):
    """Get performance overview dashboard data."""
    try:
        return service.get_performance_overview(start_date, end_date)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/partners/stats")
async def get_partner_analytics(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
):
    """Get partner analytics dashboard data."""
    try:
        return service.get_partner_analytics(start_date, end_date)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/partners/head-to-head")
async def get_head_to_head(
    partner1_id: int = Query(...),
    partner2_id: int = Query(...),
):
    """Get head-to-head comparison between two partners."""
    try:
        result = service.get_head_to_head(partner1_id, partner2_id)
        if not result:
            raise HTTPException(status_code=404, detail="One or both partners not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/readiness/trends")
async def get_readiness_trends(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
):
    """Get readiness and recovery analytics."""
    try:
        return service.get_readiness_trends(start_date, end_date)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/whoop/analytics")
async def get_whoop_analytics(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
):
    """Get Whoop fitness tracker analytics."""
    try:
        return service.get_whoop_analytics(start_date, end_date)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/techniques/breakdown")
async def get_technique_analytics(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
):
    """Get technique mastery analytics."""
    try:
        return service.get_technique_analytics(start_date, end_date)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/consistency/metrics")
async def get_consistency_analytics(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
):
    """Get training consistency analytics."""
    try:
        return service.get_consistency_analytics(start_date, end_date)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/milestones")
async def get_milestones():
    """Get progression and milestone data."""
    try:
        return service.get_milestones()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/instructors/insights")
async def get_instructor_analytics(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
):
    """Get instructor insights analytics."""
    try:
        return service.get_instructor_analytics(start_date, end_date)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
