"""Analytics and dashboard endpoints."""

import logging
import traceback
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from rivaflow.core.dependencies import get_current_user
from rivaflow.core.exceptions import NotFoundError, RivaFlowException
from rivaflow.core.services.analytics_service import AnalyticsService
from rivaflow.core.services.fight_dynamics_service import FightDynamicsService
from rivaflow.core.services.whoop_analytics_engine import WhoopAnalyticsEngine
from rivaflow.core.utils.cache import cached

logger = logging.getLogger(__name__)

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)
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
@limiter.limit("60/minute")
def get_performance_overview(
    request: Request,
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
@limiter.limit("60/minute")
def get_partner_analytics(
    request: Request,
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
@limiter.limit("60/minute")
def get_head_to_head(
    request: Request,
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
@limiter.limit("60/minute")
def get_readiness_trends(
    request: Request,
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
@limiter.limit("60/minute")
def get_whoop_analytics(
    request: Request,
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
@limiter.limit("60/minute")
def get_technique_analytics(
    request: Request,
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
@limiter.limit("60/minute")
def get_consistency_analytics(
    request: Request,
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
@limiter.limit("60/minute")
def get_milestones(request: Request, current_user: dict = Depends(get_current_user)):
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
@limiter.limit("60/minute")
def get_instructor_analytics(
    request: Request,
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


@cached(ttl_seconds=600, key_prefix="analytics_duration")
def _get_duration_analytics_cached(
    user_id: int,
    start_date: date | None = None,
    end_date: date | None = None,
    types: list[str] | None = None,
):
    """Cached helper for duration analytics. Cache TTL: 10 minutes."""
    return service.get_duration_analytics(
        user_id=user_id, start_date=start_date, end_date=end_date, types=types
    )


@cached(ttl_seconds=600, key_prefix="analytics_time_of_day")
def _get_time_of_day_cached(
    user_id: int,
    start_date: date | None = None,
    end_date: date | None = None,
    types: list[str] | None = None,
):
    """Cached helper for time of day patterns. Cache TTL: 10 minutes."""
    return service.get_time_of_day_patterns(
        user_id=user_id, start_date=start_date, end_date=end_date, types=types
    )


@cached(ttl_seconds=600, key_prefix="analytics_gym_comparison")
def _get_gym_comparison_cached(
    user_id: int,
    start_date: date | None = None,
    end_date: date | None = None,
    types: list[str] | None = None,
):
    """Cached helper for gym comparison. Cache TTL: 10 minutes."""
    return service.get_gym_comparison(
        user_id=user_id, start_date=start_date, end_date=end_date, types=types
    )


@cached(ttl_seconds=600, key_prefix="analytics_class_type")
def _get_class_type_effectiveness_cached(
    user_id: int,
    start_date: date | None = None,
    end_date: date | None = None,
):
    """Cached helper for class type effectiveness. Cache TTL: 10 minutes."""
    return service.get_class_type_effectiveness(
        user_id=user_id, start_date=start_date, end_date=end_date
    )


@cached(ttl_seconds=600, key_prefix="analytics_weight")
def _get_weight_trend_cached(
    user_id: int,
    start_date: date | None = None,
    end_date: date | None = None,
):
    """Cached helper for weight trend. Cache TTL: 10 minutes."""
    return service.get_weight_trend(
        user_id=user_id, start_date=start_date, end_date=end_date
    )


@cached(ttl_seconds=600, key_prefix="analytics_calendar")
def _get_training_calendar_cached(
    user_id: int,
    start_date: date | None = None,
    end_date: date | None = None,
    types: list[str] | None = None,
):
    """Cached helper for training calendar. Cache TTL: 10 minutes."""
    return service.get_training_frequency_heatmap(
        user_id=user_id, start_date=start_date, end_date=end_date, types=types
    )


@cached(ttl_seconds=600, key_prefix="analytics_belt_dist")
def _get_partner_belt_distribution_cached(user_id: int):
    """Cached helper for partner belt distribution. Cache TTL: 10 minutes."""
    return service.get_partner_belt_distribution(user_id=user_id)


@router.get("/duration/trends")
@limiter.limit("60/minute")
def get_duration_analytics(
    request: Request,
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    types: list[str] | None = Query(
        None, description="Filter by class types (e.g., gi, no-gi, s&c)"
    ),
    current_user: dict = Depends(get_current_user),
):
    """Get duration analytics with trends. Cached for 10 minutes."""
    try:
        return _get_duration_analytics_cached(
            user_id=current_user["id"],
            start_date=start_date,
            end_date=end_date,
            types=types,
        )
    except (RivaFlowException, HTTPException):
        raise
    except (ValueError, KeyError, TypeError) as e:
        logger.error(f"Error in get_duration_analytics: {type(e).__name__}: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500, detail=f"Analytics error: {type(e).__name__}: {str(e)}"
        )


@router.get("/time-of-day/patterns")
@limiter.limit("60/minute")
def get_time_of_day_patterns(
    request: Request,
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    types: list[str] | None = Query(
        None, description="Filter by class types (e.g., gi, no-gi, s&c)"
    ),
    current_user: dict = Depends(get_current_user),
):
    """Get time of day performance patterns. Cached for 10 minutes."""
    try:
        return _get_time_of_day_cached(
            user_id=current_user["id"],
            start_date=start_date,
            end_date=end_date,
            types=types,
        )
    except (RivaFlowException, HTTPException):
        raise
    except (ValueError, KeyError, TypeError) as e:
        logger.error(f"Error in get_time_of_day_patterns: {type(e).__name__}: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500, detail=f"Analytics error: {type(e).__name__}: {str(e)}"
        )


@router.get("/gyms/comparison")
@limiter.limit("60/minute")
def get_gym_comparison(
    request: Request,
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    types: list[str] | None = Query(
        None, description="Filter by class types (e.g., gi, no-gi, s&c)"
    ),
    current_user: dict = Depends(get_current_user),
):
    """Get gym comparison metrics. Cached for 10 minutes."""
    try:
        return _get_gym_comparison_cached(
            user_id=current_user["id"],
            start_date=start_date,
            end_date=end_date,
            types=types,
        )
    except (RivaFlowException, HTTPException):
        raise
    except (ValueError, KeyError, TypeError) as e:
        logger.error(f"Error in get_gym_comparison: {type(e).__name__}: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500, detail=f"Analytics error: {type(e).__name__}: {str(e)}"
        )


@router.get("/class-types/effectiveness")
@limiter.limit("60/minute")
def get_class_type_effectiveness(
    request: Request,
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    current_user: dict = Depends(get_current_user),
):
    """Get class type effectiveness metrics. Cached for 10 minutes."""
    try:
        return _get_class_type_effectiveness_cached(
            user_id=current_user["id"],
            start_date=start_date,
            end_date=end_date,
        )
    except (RivaFlowException, HTTPException):
        raise
    except (ValueError, KeyError, TypeError) as e:
        logger.error(
            f"Error in get_class_type_effectiveness: {type(e).__name__}: {str(e)}"
        )
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500, detail=f"Analytics error: {type(e).__name__}: {str(e)}"
        )


@router.get("/weight/trend")
@limiter.limit("60/minute")
def get_weight_trend(
    request: Request,
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    current_user: dict = Depends(get_current_user),
):
    """Get weight trend with 7-day SMA. Cached for 10 minutes."""
    try:
        return _get_weight_trend_cached(
            user_id=current_user["id"],
            start_date=start_date,
            end_date=end_date,
        )
    except (RivaFlowException, HTTPException):
        raise
    except (ValueError, KeyError, TypeError) as e:
        logger.error(f"Error in get_weight_trend: {type(e).__name__}: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500, detail=f"Analytics error: {type(e).__name__}: {str(e)}"
        )


@router.get("/training-calendar")
@limiter.limit("60/minute")
def get_training_calendar(
    request: Request,
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    types: list[str] | None = Query(
        None, description="Filter by class types (e.g., gi, no-gi, s&c)"
    ),
    current_user: dict = Depends(get_current_user),
):
    """Get training frequency calendar data. Cached for 10 minutes."""
    try:
        return _get_training_calendar_cached(
            user_id=current_user["id"],
            start_date=start_date,
            end_date=end_date,
            types=types,
        )
    except (RivaFlowException, HTTPException):
        raise
    except (ValueError, KeyError, TypeError) as e:
        logger.error(f"Error in get_training_calendar: {type(e).__name__}: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500, detail=f"Analytics error: {type(e).__name__}: {str(e)}"
        )


@router.get("/partners/belt-distribution")
@limiter.limit("60/minute")
def get_partner_belt_distribution(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Get partner belt rank distribution. Cached for 10 minutes."""
    try:
        return _get_partner_belt_distribution_cached(
            user_id=current_user["id"],
        )
    except (RivaFlowException, HTTPException):
        raise
    except (ValueError, KeyError, TypeError) as e:
        logger.error(
            f"Error in get_partner_belt_distribution: {type(e).__name__}: {str(e)}"
        )
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500, detail=f"Analytics error: {type(e).__name__}: {str(e)}"
        )


# ============================================================================
# INSIGHTS ENGINE (Phase 2) - Deep analytics endpoints
# ============================================================================


@cached(ttl_seconds=300, key_prefix="insights_summary")
def _get_insights_summary_cached(user_id: int):
    """Cached helper for insights summary. Cache TTL: 5 minutes."""
    return service.get_insights_summary(user_id=user_id)


@cached(ttl_seconds=600, key_prefix="insights_readiness_corr")
def _get_readiness_correlation_cached(
    user_id: int,
    start_date: date | None = None,
    end_date: date | None = None,
):
    """Cached helper for readiness correlation. Cache TTL: 10 minutes."""
    return service.get_readiness_performance_correlation(
        user_id=user_id, start_date=start_date, end_date=end_date
    )


@cached(ttl_seconds=600, key_prefix="insights_training_load")
def _get_training_load_cached(user_id: int, days: int = 90):
    """Cached helper for training load. Cache TTL: 10 minutes."""
    return service.get_training_load_management(user_id=user_id, days=days)


@cached(ttl_seconds=600, key_prefix="insights_technique_eff")
def _get_technique_effectiveness_cached(
    user_id: int,
    start_date: date | None = None,
    end_date: date | None = None,
):
    """Cached helper for technique effectiveness. Cache TTL: 10 minutes."""
    return service.get_technique_effectiveness(
        user_id=user_id, start_date=start_date, end_date=end_date
    )


@cached(ttl_seconds=600, key_prefix="insights_partner_prog")
def _get_partner_progression_cached(user_id: int, partner_id: int):
    """Cached helper for partner progression. Cache TTL: 10 minutes."""
    return service.get_partner_progression(user_id=user_id, partner_id=partner_id)


@cached(ttl_seconds=600, key_prefix="insights_quality")
def _get_session_quality_cached(
    user_id: int,
    start_date: date | None = None,
    end_date: date | None = None,
):
    """Cached helper for session quality. Cache TTL: 10 minutes."""
    return service.get_session_quality_scores(
        user_id=user_id, start_date=start_date, end_date=end_date
    )


@cached(ttl_seconds=300, key_prefix="insights_risk")
def _get_overtraining_risk_cached(user_id: int):
    """Cached helper for overtraining risk. Cache TTL: 5 minutes."""
    return service.get_overtraining_risk(user_id=user_id)


@cached(ttl_seconds=600, key_prefix="insights_recovery")
def _get_recovery_insights_cached(user_id: int, days: int = 90):
    """Cached helper for recovery insights. Cache TTL: 10 minutes."""
    return service.get_recovery_insights(user_id=user_id, days=days)


@router.get("/insights/summary")
@limiter.limit("60/minute")
def get_insights_summary(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Get insights dashboard summary. Cached for 5 minutes."""
    try:
        return _get_insights_summary_cached(user_id=current_user["id"])
    except (RivaFlowException, HTTPException):
        raise
    except (ValueError, KeyError, TypeError) as e:
        logger.error(f"Error in get_insights_summary: {type(e).__name__}: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500, detail=f"Analytics error: {type(e).__name__}: {str(e)}"
        )


@router.get("/insights/readiness-correlation")
@limiter.limit("60/minute")
def get_readiness_correlation(
    request: Request,
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    current_user: dict = Depends(get_current_user),
):
    """Get readiness × performance correlation. Cached for 10 minutes."""
    try:
        return _get_readiness_correlation_cached(
            user_id=current_user["id"],
            start_date=start_date,
            end_date=end_date,
        )
    except (RivaFlowException, HTTPException):
        raise
    except (ValueError, KeyError, TypeError) as e:
        logger.error(
            f"Error in get_readiness_correlation: {type(e).__name__}: {str(e)}"
        )
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500, detail=f"Analytics error: {type(e).__name__}: {str(e)}"
        )


@router.get("/insights/training-load")
@limiter.limit("60/minute")
def get_training_load(
    request: Request,
    days: int = Query(default=90, ge=7, le=365),
    current_user: dict = Depends(get_current_user),
):
    """Get ACWR training load management. Cached for 10 minutes."""
    try:
        return _get_training_load_cached(user_id=current_user["id"], days=days)
    except (RivaFlowException, HTTPException):
        raise
    except (ValueError, KeyError, TypeError) as e:
        logger.error(f"Error in get_training_load: {type(e).__name__}: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500, detail=f"Analytics error: {type(e).__name__}: {str(e)}"
        )


@router.get("/insights/technique-effectiveness")
@limiter.limit("60/minute")
def get_technique_effectiveness_insights(
    request: Request,
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    current_user: dict = Depends(get_current_user),
):
    """Get technique effectiveness with quadrant analysis. Cached for 10 minutes."""
    try:
        return _get_technique_effectiveness_cached(
            user_id=current_user["id"],
            start_date=start_date,
            end_date=end_date,
        )
    except (RivaFlowException, HTTPException):
        raise
    except (ValueError, KeyError, TypeError) as e:
        logger.error(
            f"Error in get_technique_effectiveness: {type(e).__name__}: {str(e)}"
        )
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500, detail=f"Analytics error: {type(e).__name__}: {str(e)}"
        )


@router.get("/insights/partner-progression/{partner_id}")
@limiter.limit("60/minute")
def get_partner_progression(
    request: Request,
    partner_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Get rolling progression against a specific partner. Cached for 10 minutes."""
    try:
        return _get_partner_progression_cached(
            user_id=current_user["id"], partner_id=partner_id
        )
    except (RivaFlowException, HTTPException):
        raise
    except (ValueError, KeyError, TypeError) as e:
        logger.error(f"Error in get_partner_progression: {type(e).__name__}: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500, detail=f"Analytics error: {type(e).__name__}: {str(e)}"
        )


@router.get("/insights/session-quality")
@limiter.limit("60/minute")
def get_session_quality(
    request: Request,
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    current_user: dict = Depends(get_current_user),
):
    """Get session quality scores. Cached for 10 minutes."""
    try:
        return _get_session_quality_cached(
            user_id=current_user["id"],
            start_date=start_date,
            end_date=end_date,
        )
    except (RivaFlowException, HTTPException):
        raise
    except (ValueError, KeyError, TypeError) as e:
        logger.error(f"Error in get_session_quality: {type(e).__name__}: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500, detail=f"Analytics error: {type(e).__name__}: {str(e)}"
        )


@router.get("/insights/overtraining-risk")
@limiter.limit("60/minute")
def get_overtraining_risk(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Get overtraining risk assessment. Cached for 5 minutes."""
    try:
        return _get_overtraining_risk_cached(user_id=current_user["id"])
    except (RivaFlowException, HTTPException):
        raise
    except (ValueError, KeyError, TypeError) as e:
        logger.error(f"Error in get_overtraining_risk: {type(e).__name__}: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500, detail=f"Analytics error: {type(e).__name__}: {str(e)}"
        )


@router.get("/insights/recovery")
@limiter.limit("60/minute")
def get_recovery_insights(
    request: Request,
    days: int = Query(default=90, ge=7, le=365),
    current_user: dict = Depends(get_current_user),
):
    """Get recovery insights. Cached for 10 minutes."""
    try:
        return _get_recovery_insights_cached(user_id=current_user["id"], days=days)
    except (RivaFlowException, HTTPException):
        raise
    except (ValueError, KeyError, TypeError) as e:
        logger.error(f"Error in get_recovery_insights: {type(e).__name__}: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500, detail=f"Analytics error: {type(e).__name__}: {str(e)}"
        )


@router.get("/fight-dynamics/heatmap")
@limiter.limit("60/minute")
def get_fight_dynamics_heatmap(
    request: Request,
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
@limiter.limit("60/minute")
def get_fight_dynamics_insights(
    request: Request,
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


# ============================================================================
# WHOOP PERFORMANCE SCIENCE (Phase 3)
# ============================================================================

whoop_analytics = WhoopAnalyticsEngine()


@cached(ttl_seconds=600, key_prefix="whoop_perf_corr")
def _get_whoop_performance_correlation_cached(user_id: int, days: int = 90):
    return {
        "recovery_correlation": whoop_analytics.get_recovery_performance_correlation(
            user_id, days
        ),
        "hrv_predictor": whoop_analytics.get_hrv_performance_predictor(user_id, days),
    }


@cached(ttl_seconds=600, key_prefix="whoop_efficiency")
def _get_whoop_efficiency_cached(user_id: int, days: int = 90):
    return {
        "strain_efficiency": whoop_analytics.get_strain_efficiency(user_id, days),
        "sleep_analysis": whoop_analytics.get_sleep_performance_analysis(user_id, days),
    }


@cached(ttl_seconds=600, key_prefix="whoop_cardiovascular")
def _get_whoop_cardiovascular_cached(user_id: int, days: int = 90):
    return whoop_analytics.get_cardiovascular_drift(user_id, days)


@router.get("/whoop/performance-correlation")
@limiter.limit("60/minute")
def get_whoop_performance_correlation(
    request: Request,
    days: int = Query(default=90, ge=7, le=365),
    current_user: dict = Depends(get_current_user),
):
    """Recovery + HRV performance correlation. Cached 10 min."""
    try:
        return _get_whoop_performance_correlation_cached(
            user_id=current_user["id"], days=days
        )
    except (RivaFlowException, HTTPException):
        raise
    except (ValueError, KeyError, TypeError) as e:
        logger.error(
            f"Error in whoop performance correlation:" f" {type(e).__name__}: {str(e)}"
        )
        raise HTTPException(
            status_code=500,
            detail=f"Analytics error: {type(e).__name__}: {str(e)}",
        )


@router.get("/whoop/efficiency")
@limiter.limit("60/minute")
def get_whoop_efficiency(
    request: Request,
    days: int = Query(default=90, ge=7, le=365),
    current_user: dict = Depends(get_current_user),
):
    """Strain efficiency + sleep analysis. Cached 10 min."""
    try:
        return _get_whoop_efficiency_cached(user_id=current_user["id"], days=days)
    except (RivaFlowException, HTTPException):
        raise
    except (ValueError, KeyError, TypeError) as e:
        logger.error(f"Error in whoop efficiency:" f" {type(e).__name__}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Analytics error: {type(e).__name__}: {str(e)}",
        )


@router.get("/whoop/cardiovascular")
@limiter.limit("60/minute")
def get_whoop_cardiovascular(
    request: Request,
    days: int = Query(default=90, ge=7, le=365),
    current_user: dict = Depends(get_current_user),
):
    """Cardiovascular drift (RHR trend). Cached 10 min."""
    try:
        return _get_whoop_cardiovascular_cached(user_id=current_user["id"], days=days)
    except (RivaFlowException, HTTPException):
        raise
    except (ValueError, KeyError, TypeError) as e:
        logger.error(f"Error in whoop cardiovascular:" f" {type(e).__name__}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Analytics error: {type(e).__name__}: {str(e)}",
        )


@cached(ttl_seconds=600, key_prefix="whoop_sleep_debt")
def _get_whoop_sleep_debt_cached(user_id: int, days: int = 90):
    return whoop_analytics.get_sleep_debt_tracker(user_id, days)


@cached(ttl_seconds=600, key_prefix="whoop_readiness_model")
def _get_whoop_readiness_model_cached(user_id: int, days: int = 90):
    return whoop_analytics.get_recovery_readiness_model(user_id, days)


@router.get("/whoop/sleep-debt")
@limiter.limit("60/minute")
def get_whoop_sleep_debt(
    request: Request,
    days: int = Query(default=90, ge=7, le=365),
    current_user: dict = Depends(get_current_user),
):
    """Sleep debt vs training volume. Cached 10 min."""
    try:
        return _get_whoop_sleep_debt_cached(user_id=current_user["id"], days=days)
    except (RivaFlowException, HTTPException):
        raise
    except (ValueError, KeyError, TypeError) as e:
        logger.error(f"Error in whoop sleep debt: {type(e).__name__}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Analytics error: {type(e).__name__}: {str(e)}",
        )


@router.get("/whoop/readiness-model")
@limiter.limit("60/minute")
def get_whoop_readiness_model(
    request: Request,
    days: int = Query(default=90, ge=7, le=365),
    current_user: dict = Depends(get_current_user),
):
    """Recovery readiness model. Cached 10 min."""
    try:
        return _get_whoop_readiness_model_cached(user_id=current_user["id"], days=days)
    except (RivaFlowException, HTTPException):
        raise
    except (ValueError, KeyError, TypeError) as e:
        logger.error(
            f"Error in whoop readiness model:" f" {type(e).__name__}: {str(e)}"
        )
        raise HTTPException(
            status_code=500,
            detail=f"Analytics error: {type(e).__name__}: {str(e)}",
        )
