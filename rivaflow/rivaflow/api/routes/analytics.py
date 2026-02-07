"""Analytics and dashboard endpoints."""

import logging
import traceback
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query

from rivaflow.core.dependencies import get_current_user
from rivaflow.core.exceptions import NotFoundError, RivaFlowException
from rivaflow.core.services.analytics_service import AnalyticsService
from rivaflow.core.services.fight_dynamics_service import FightDynamicsService
from rivaflow.core.utils.cache import cached

logger = logging.getLogger(__name__)

router = APIRouter()
service = AnalyticsService()
fight_dynamics_service = FightDynamicsService()


@cached(ttl_seconds=600, key_prefix="analytics_performance")
def _get_performance_overview_cached(
    user_id: int,
    start_date: date | None = None,
    end_date: date | None = None,
    types: list[str] | None = None,
):
    """
    Cached helper for performance overview.
    Cache TTL: 10 minutes
    """
    return service.get_performance_overview(
        user_id=user_id, start_date=start_date, end_date=end_date, types=types
    )


@cached(ttl_seconds=600, key_prefix="analytics_partners")
def _get_partner_analytics_cached(
    user_id: int,
    start_date: date | None = None,
    end_date: date | None = None,
    types: list[str] | None = None,
):
    """
    Cached helper for partner analytics.
    Cache TTL: 10 minutes
    """
    return service.get_partner_analytics(
        user_id=user_id, start_date=start_date, end_date=end_date, types=types
    )


@cached(ttl_seconds=600, key_prefix="analytics_techniques")
def _get_technique_analytics_cached(
    user_id: int,
    start_date: date | None = None,
    end_date: date | None = None,
    types: list[str] | None = None,
):
    """
    Cached helper for technique analytics.
    Cache TTL: 10 minutes
    """
    return service.get_technique_analytics(
        user_id=user_id, start_date=start_date, end_date=end_date, types=types
    )


@router.get("/performance-overview")
async def get_performance_overview(
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    types: list[str] | None = Query(
        None, description="Filter by class types (e.g., gi, no-gi, s&c)"
    ),
    current_user: dict = Depends(get_current_user),
):
    """Get performance overview dashboard data. Cached for 10 minutes."""
    # Validate date range
    if start_date and end_date:
        if start_date > end_date:
            raise HTTPException(
                status_code=400, detail="start_date must be before end_date"
            )
        if (end_date - start_date).days > 730:  # 2 years max
            raise HTTPException(
                status_code=400, detail="Date range cannot exceed 2 years"
            )

    try:
        return _get_performance_overview_cached(
            user_id=current_user["id"],
            start_date=start_date,
            end_date=end_date,
            types=types,
        )
    except (RivaFlowException, HTTPException):
        raise
    except (ValueError, KeyError, TypeError) as e:
        logger.error(f"Error in get_performance_overview: {type(e).__name__}: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500, detail=f"Analytics error: {type(e).__name__}: {str(e)}"
        )


@router.get("/partners/stats")
async def get_partner_analytics(
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    types: list[str] | None = Query(
        None, description="Filter by class types (e.g., gi, no-gi, s&c)"
    ),
    current_user: dict = Depends(get_current_user),
):
    """Get partner analytics dashboard data. Cached for 10 minutes."""
    try:
        return _get_partner_analytics_cached(
            user_id=current_user["id"],
            start_date=start_date,
            end_date=end_date,
            types=types,
        )
    except (RivaFlowException, HTTPException):
        raise
    except (ValueError, KeyError, TypeError) as e:
        logger.error(f"Error in get_partner_analytics: {type(e).__name__}: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500, detail=f"Analytics error: {type(e).__name__}: {str(e)}"
        )


@router.get("/partners/head-to-head")
async def get_head_to_head(
    partner1_id: int = Query(...),
    partner2_id: int = Query(...),
    current_user: dict = Depends(get_current_user),
):
    """Get head-to-head comparison between two partners."""
    try:
        result = service.get_head_to_head(
            user_id=current_user["id"], partner1_id=partner1_id, partner2_id=partner2_id
        )
        if not result:
            raise NotFoundError("One or both partners not found")
        return result
    except HTTPException:
        raise


@router.get("/readiness/trends")
async def get_readiness_trends(
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    types: list[str] | None = Query(
        None, description="Filter by class types (e.g., gi, no-gi, s&c)"
    ),
    current_user: dict = Depends(get_current_user),
):
    """Get readiness and recovery analytics."""
    return service.get_readiness_trends(
        user_id=current_user["id"],
        start_date=start_date,
        end_date=end_date,
        types=types,
    )


@router.get("/whoop/analytics")
async def get_whoop_analytics(
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    types: list[str] | None = Query(
        None, description="Filter by class types (e.g., gi, no-gi, s&c)"
    ),
    current_user: dict = Depends(get_current_user),
):
    """Get Whoop fitness tracker analytics."""
    return service.get_whoop_analytics(
        user_id=current_user["id"],
        start_date=start_date,
        end_date=end_date,
        types=types,
    )


@router.get("/techniques/breakdown")
async def get_technique_analytics(
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    types: list[str] | None = Query(
        None, description="Filter by class types (e.g., gi, no-gi, s&c)"
    ),
    current_user: dict = Depends(get_current_user),
):
    """Get technique mastery analytics. Cached for 10 minutes."""
    try:
        return _get_technique_analytics_cached(
            user_id=current_user["id"],
            start_date=start_date,
            end_date=end_date,
            types=types,
        )
    except (RivaFlowException, HTTPException):
        raise
    except (ValueError, KeyError, TypeError) as e:
        logger.error(f"Error in get_technique_analytics: {type(e).__name__}: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500, detail=f"Analytics error: {type(e).__name__}: {str(e)}"
        )


@router.get("/consistency/metrics")
async def get_consistency_analytics(
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    types: list[str] | None = Query(
        None, description="Filter by class types (e.g., gi, no-gi, s&c)"
    ),
    current_user: dict = Depends(get_current_user),
):
    """Get training consistency analytics."""
    try:
        return service.get_consistency_analytics(
            user_id=current_user["id"],
            start_date=start_date,
            end_date=end_date,
            types=types,
        )
    except (RivaFlowException, HTTPException):
        raise
    except (ValueError, KeyError, TypeError) as e:
        logger.error(
            f"Error in get_consistency_analytics: {type(e).__name__}: {str(e)}"
        )
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500, detail=f"Analytics error: {type(e).__name__}: {str(e)}"
        )


@router.get("/milestones")
async def get_milestones(current_user: dict = Depends(get_current_user)):
    """Get progression and milestone data."""
    try:
        return service.get_milestones(user_id=current_user["id"])
    except (RivaFlowException, HTTPException):
        raise
    except (ValueError, KeyError, TypeError) as e:
        logger.error(f"Error in get_milestones: {type(e).__name__}: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500, detail=f"Analytics error: {type(e).__name__}: {str(e)}"
        )


@router.get("/instructors/insights")
async def get_instructor_analytics(
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    types: list[str] | None = Query(
        None, description="Filter by class types (e.g., gi, no-gi, s&c)"
    ),
    current_user: dict = Depends(get_current_user),
):
    """Get instructor insights analytics."""
    try:
        return service.get_instructor_analytics(
            user_id=current_user["id"],
            start_date=start_date,
            end_date=end_date,
            types=types,
        )
    except (RivaFlowException, HTTPException):
        raise
    except (ValueError, KeyError, TypeError) as e:
        logger.error(f"Error in get_instructor_analytics: {type(e).__name__}: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500, detail=f"Analytics error: {type(e).__name__}: {str(e)}"
        )


@router.get("/fight-dynamics/heatmap")
async def get_fight_dynamics_heatmap(
    view: str = Query(
        default="weekly",
        pattern="^(weekly|monthly)$",
        description="View type: weekly or monthly",
    ),
    weeks: int = Query(
        default=8, ge=1, le=52, description="Number of weeks (weekly view)"
    ),
    months: int = Query(
        default=6, ge=1, le=24, description="Number of months (monthly view)"
    ),
    current_user: dict = Depends(get_current_user),
):
    """Get aggregated attack/defence data for heatmap display."""
    try:
        return fight_dynamics_service.get_heatmap_data(
            user_id=current_user["id"],
            view=view,
            weeks=weeks,
            months=months,
        )
    except (RivaFlowException, HTTPException):
        raise
    except (ValueError, KeyError, TypeError) as e:
        logger.error(
            f"Error in get_fight_dynamics_heatmap: {type(e).__name__}: {str(e)}"
        )
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Analytics error: {type(e).__name__}: {str(e)}",
        )


@router.get("/fight-dynamics/insights")
async def get_fight_dynamics_insights(
    current_user: dict = Depends(get_current_user),
):
    """Get auto-generated fight dynamics insights.

    Compares last 4 weeks to previous 4 weeks.
    Only generates insights when 3+ sessions have fight dynamics data.
    """
    try:
        return fight_dynamics_service.get_insights(
            user_id=current_user["id"],
        )
    except (RivaFlowException, HTTPException):
        raise
    except (ValueError, KeyError, TypeError) as e:
        logger.error(
            f"Error in get_fight_dynamics_insights: {type(e).__name__}: {str(e)}"
        )
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Analytics error: {type(e).__name__}: {str(e)}",
        )
