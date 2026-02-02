# Analytics Service Architecture

## Overview

The analytics functionality has been refactored from a single monolithic `AnalyticsService` (1050 lines) into four focused services organized by domain responsibility.

## Service Breakdown

### 1. PerformanceAnalyticsService
**File:** `rivaflow/core/services/performance_analytics.py`
**Responsibilities:** Training performance metrics, partner statistics, instructor insights

**Methods:**
- `get_performance_overview()` - Submission success, training volume, performance by belt
- `get_partner_analytics()` - Partner matrix, diversity metrics, session distribution
- `get_head_to_head()` - Head-to-head partner comparison
- `get_instructor_analytics()` - Performance metrics grouped by instructor

**Key Features:**
- Monthly submission ratios with division-by-zero protection
- Training volume calendar (daily heatmaps)
- Top submissions tracking (movement-based)
- Performance segmented by belt rank periods
- Partner diversity metrics (new vs recurring)

### 2. ReadinessAnalyticsService
**File:** `rivaflow/core/services/readiness_analytics.py`
**Responsibilities:** Readiness tracking, recovery analysis, WHOOP integration

**Methods:**
- `get_readiness_trends()` - Daily readiness scores, training load correlation, recovery patterns
- `get_whoop_analytics()` - Strain analysis, heart rate zones, calorie burn

**Key Features:**
- Composite readiness score tracking (sleep, stress, soreness, energy)
- Training load vs readiness correlation
- Recovery patterns by day of week
- Injury/hotspot timeline
- Weight tracking with statistics
- WHOOP strain vs next-day readiness correlation
- Heart rate zone analysis by class type

### 3. TechniqueAnalyticsService
**File:** `rivaflow/core/services/technique_analytics.py`
**Responsibilities:** Technique mastery tracking and analysis

**Methods:**
- `get_technique_analytics()` - Category breakdown, stale techniques, gi vs no-gi comparison

**Key Features:**
- Technique usage by category (guard passing, sweeps, submissions, etc.)
- Stale technique detection (30-day threshold)
- Gi vs No-Gi technique comparison (top 10 each)
- Unique technique count tracking

### 4. StreakAnalyticsService
**File:** `rivaflow/core/services/streak_analytics.py`
**Responsibilities:** Training consistency, streaks, progression milestones

**Methods:**
- `get_consistency_analytics()` - Weekly volume, class type distribution, gym breakdown
- `get_milestones()` - Belt progression timeline, personal records, lifetime stats

**Key Features:**
- Current and longest training streak calculation
- Weekly volume tracking (sessions/hours/rolls)
- Class type distribution analysis
- Gym-based training breakdown
- Belt progression timeline with hours at each belt
- Personal records (most rolls, longest session, best sub ratio)
- Rolling totals (lifetime, current belt, this year)

## Backward Compatibility

The original `AnalyticsService` class has been maintained as a **facade** that delegates to the focused services.

**Old usage (still works):**
```python
from rivaflow.core.services.analytics_service import AnalyticsService

analytics = AnalyticsService()
data = analytics.get_performance_overview(user_id=1)
```

**New usage (direct access to focused services):**
```python
from rivaflow.core.services.performance_analytics import PerformanceAnalyticsService

performance = PerformanceAnalyticsService()
data = performance.get_performance_overview(user_id=1)
```

## Architecture Benefits

### Before Refactoring
- **1 file, 1050 lines** - Hard to navigate and maintain
- All analytics logic mixed together
- Difficult to test individual domains
- Unclear separation of concerns

### After Refactoring
- **5 files, ~1100 lines total** - Better organized
- Clear domain boundaries
- Each service can be tested independently
- Easier to extend with new analytics features
- Maintains backward compatibility via facade pattern

## File Structure

```
rivaflow/core/services/
├── analytics_service.py           # Facade (maintains backward compatibility)
├── performance_analytics.py       # Performance & partner analytics
├── readiness_analytics.py         # Readiness & WHOOP analytics
├── technique_analytics.py         # Technique mastery analytics
└── streak_analytics.py            # Consistency & milestone analytics
```

## Usage in API Routes

The API routes continue to use `AnalyticsService` without any changes:

```python
# api/routes/analytics.py
from rivaflow.core.services.analytics_service import AnalyticsService

@router.get("/performance")
async def get_performance(user_id: int = Depends(get_current_user_id)):
    analytics = AnalyticsService()
    return analytics.get_performance_overview(user_id)
```

## Testing Strategy

Each focused service can now be tested independently:

```python
# tests/core/test_performance_analytics.py
from rivaflow.core.services.performance_analytics import PerformanceAnalyticsService

def test_performance_overview():
    service = PerformanceAnalyticsService()
    result = service.get_performance_overview(user_id=1)
    assert "submission_success_over_time" in result
```

## Future Improvements

1. **Caching** - Add caching to expensive analytics queries
2. **Async Support** - Convert to async methods for better performance
3. **Parallel Queries** - Execute independent queries in parallel
4. **Query Optimization** - Further reduce N+1 queries
5. **Real-time Updates** - Add WebSocket support for live dashboards

## Migration Notes

No migration needed - the facade pattern ensures all existing code continues to work unchanged.

---

**Last Updated:** 2026-02-02
**Related:** Task #8 from BETA_READINESS_REPORT.md
