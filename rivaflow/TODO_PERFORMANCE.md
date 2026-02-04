# Performance Optimization TODOs

## Dashboard Parallelization (Post-Launch)
**File**: `rivaflow/api/routes/dashboard.py`
**Priority**: Medium (3x performance improvement)

The dashboard summary endpoint makes 7+ sequential service calls that could be parallelized:
- Convert service methods to async
- Use `asyncio.gather()` to run in parallel
- Expected improvement: 800ms → 300ms

**Implementation**:
```python
# Convert to:
performance, session_streak, checkin_streak, recent_sessions, ... = await asyncio.gather(
    analytics.get_performance_overview_async(...),
    streak_service.get_streak_async(...),
    ...
)
```

**Note**: Requires refactoring services to be async-compatible. Safe to defer to post-launch optimization phase.

## N+1 Glossary Lookups Fix
**File**: `rivaflow/core/services/performance_analytics.py:99-116`
**Priority**: Medium (reduces queries by 5-10 per request)

Add batch lookup method to glossary_repo:
```python
def get_by_ids(self, ids: List[int]) -> List[dict]:
    placeholders = ",".join("?" * len(ids))
    query = f"SELECT * FROM movements_glossary WHERE id IN ({placeholders})"
    ...
```

## Chunked File Uploads
**File**: `rivaflow/api/routes/photos.py:107`
**Priority**: Low (current 5MB limit is acceptable for beta)

Replace full file read with chunked streaming:
```python
CHUNK_SIZE = 64 * 1024  # 64KB
async for chunk in file.stream():
    # Process chunks
```
