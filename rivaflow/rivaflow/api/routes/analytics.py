"""Analytics and dashboard endpoints."""
from fastapi import APIRouter, Query, Depends, HTTPException
from datetime import date
from typing import Optional, List
import traceback
import logging

from rivaflow.core.services.analytics_service import AnalyticsService
from rivaflow.core.dependencies import get_current_user
from rivaflow.core.exceptions import ValidationError, NotFoundError
from rivaflow.core.utils.cache import cached

logger = logging.getLogger(__name__)

router = APIRouter()
service = AnalyticsService()


@cached(ttl_seconds=600, key_prefix="analytics_performance")
def _get_performance_overview_cached(
    user_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    types: Optional[List[str]] = None,
):
    """
    Cached helper for performance overview.
    Cache TTL: 10 minutes
    """
    return service.get_performance_overview(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        types=types
    )


@cached(ttl_seconds=600, key_prefix="analytics_partners")
def _get_partner_analytics_cached(
    user_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    types: Optional[List[str]] = None,
):
    """
    Cached helper for partner analytics.
    Cache TTL: 10 minutes
    """
    return service.get_partner_analytics(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        types=types
    )


@cached(ttl_seconds=600, key_prefix="analytics_techniques")
def _get_technique_analytics_cached(
    user_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    types: Optional[List[str]] = None,
):
    """
    Cached helper for technique analytics.
    Cache TTL: 10 minutes
    """
    return service.get_technique_analytics(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        types=types
    )


@router.get("/performance-overview")
async def get_performance_overview(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    types: Optional[List[str]] = Query(None, description="Filter by class types (e.g., gi, no-gi, s&c)"),
    current_user: dict = Depends(get_current_user),
):
    """Get performance overview dashboard data. Cached for 10 minutes."""
    try:
        return _get_performance_overview_cached(
            user_id=current_user["id"],
            start_date=start_date,
            end_date=end_date,
            types=types
        )
    except Exception as e:
        logger.error(f"Error in get_performance_overview: {type(e).__name__}: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Analytics error: {type(e).__name__}: {str(e)}")


@router.get("/partners/stats")
async def get_partner_analytics(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    types: Optional[List[str]] = Query(None, description="Filter by class types (e.g., gi, no-gi, s&c)"),
    current_user: dict = Depends(get_current_user),
):
    """Get partner analytics dashboard data. Cached for 10 minutes."""
    try:
        return _get_partner_analytics_cached(
            user_id=current_user["id"],
            start_date=start_date,
            end_date=end_date,
            types=types
        )
    except Exception as e:
        logger.error(f"Error in get_partner_analytics: {type(e).__name__}: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Analytics error: {type(e).__name__}: {str(e)}")


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
    types: Optional[List[str]] = Query(None, description="Filter by class types (e.g., gi, no-gi, s&c)"),
    current_user: dict = Depends(get_current_user),
):
    """Get readiness and recovery analytics."""
    return service.get_readiness_trends(user_id=current_user["id"], start_date=start_date, end_date=end_date, types=types)


@router.get("/whoop/analytics")
async def get_whoop_analytics(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    types: Optional[List[str]] = Query(None, description="Filter by class types (e.g., gi, no-gi, s&c)"),
    current_user: dict = Depends(get_current_user),
):
    """Get Whoop fitness tracker analytics."""
    return service.get_whoop_analytics(user_id=current_user["id"], start_date=start_date, end_date=end_date, types=types)


@router.get("/techniques/breakdown")
async def get_technique_analytics(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    types: Optional[List[str]] = Query(None, description="Filter by class types (e.g., gi, no-gi, s&c)"),
    current_user: dict = Depends(get_current_user),
):
    """Get technique mastery analytics. Cached for 10 minutes."""
    try:
        return _get_technique_analytics_cached(
            user_id=current_user["id"],
            start_date=start_date,
            end_date=end_date,
            types=types
        )
    except Exception as e:
        logger.error(f"Error in get_technique_analytics: {type(e).__name__}: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Analytics error: {type(e).__name__}: {str(e)}")


@router.get("/consistency/metrics")
async def get_consistency_analytics(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    types: Optional[List[str]] = Query(None, description="Filter by class types (e.g., gi, no-gi, s&c)"),
    current_user: dict = Depends(get_current_user),
):
    """Get training consistency analytics."""
    try:
        return service.get_consistency_analytics(user_id=current_user["id"], start_date=start_date, end_date=end_date, types=types)
    except Exception as e:
        logger.error(f"Error in get_consistency_analytics: {type(e).__name__}: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Analytics error: {type(e).__name__}: {str(e)}")


@router.get("/milestones")
async def get_milestones(current_user: dict = Depends(get_current_user)):
    """Get progression and milestone data."""
    try:
        return service.get_milestones(user_id=current_user["id"])
    except Exception as e:
        logger.error(f"Error in get_milestones: {type(e).__name__}: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Analytics error: {type(e).__name__}: {str(e)}")


@router.get("/instructors/insights")
async def get_instructor_analytics(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    types: Optional[List[str]] = Query(None, description="Filter by class types (e.g., gi, no-gi, s&c)"),
    current_user: dict = Depends(get_current_user),
):
    """Get instructor insights analytics."""
    try:
        return service.get_instructor_analytics(user_id=current_user["id"], start_date=start_date, end_date=end_date, types=types)
    except Exception as e:
        logger.error(f"Error in get_instructor_analytics: {type(e).__name__}: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Analytics error: {type(e).__name__}: {str(e)}")
