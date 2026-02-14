# RivaFlow Backend Code Review

**Reviewer:** Claude Opus 4.6
**Date:** 2026-02-11
**Scope:** Full backend review of `rivaflow/rivaflow/` -- repositories, routes, services, database layer

---

## CRITICAL Priority

### C-1. Session Delete Has Cross-Connection Transaction Bug
**File:** `/Users/rubertwolff/scratch/rivaflow/rivaflow/db/repositories/session_repo.py`, lines 432-450

The `delete()` method opens its **own** `get_connection()` context, but calls `SessionRollRepository.delete_by_session()` and `SessionTechniqueRepository.delete_by_session()` which each open their **own** `get_connection()` contexts internally. This means the child record deletions and the parent session deletion happen in **separate database transactions**. If the session DELETE fails, the roll and technique records are already committed and gone -- orphan deletions with no rollback.

```python
def delete(user_id: int, session_id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        # These open SEPARATE connections/transactions!
        SessionRollRepository.delete_by_session(session_id)
        SessionTechniqueRepository.delete_by_session(session_id)
        cursor.execute(...)  # This is on a DIFFERENT connection
```

**Impact:** Data integrity violation -- related records deleted but parent session survives on error.
**Recommendation:** Pass the existing connection to child repo methods or perform all deletes in a single transaction block.

---

### C-2. Notification Repository Uses `RETURNING` Without `convert_query()` Handling
**File:** `/Users/rubertwolff/scratch/rivaflow/rivaflow/db/repositories/notification_repo.py`, line 37-41

The `create()` method uses `RETURNING` in the SQL directly with `convert_query()`. However, `convert_query()` only replaces `?` with `%s` for PostgreSQL. The `RETURNING` clause is PostgreSQL-only and will fail on SQLite. Unlike `execute_insert()` which handles this portability, the notification repo hardcodes `RETURNING`.

```python
query = convert_query("""
    INSERT INTO notifications (...) VALUES (?, ?, ?, ?, ?, ?, ?)
    RETURNING id, user_id, actor_id, ...
""")
```

**Impact:** This endpoint crashes on SQLite (local dev/tests).
**Recommendation:** Use `execute_insert()` + a separate SELECT, or add SQLite fallback using `lastrowid`.

---

### C-3. Auth Service Registration Has Non-Atomic Multi-Transaction Writes
**File:** `/Users/rubertwolff/scratch/rivaflow/rivaflow/core/services/auth_service.py`, lines 95-176

User registration performs user creation, profile creation, and streak initialization each in **separate** `get_connection()` blocks (separate transactions). The manual cleanup on failure (`DELETE FROM users WHERE id = ?`) runs in yet another separate transaction. If the application crashes mid-registration, partial data will persist. Worse, the manual cleanup `DELETE FROM users` bypasses CASCADE constraints in SQLite (SQLite requires `PRAGMA foreign_keys = ON` which isn't set).

**Impact:** Orphaned partial user data on registration failures.
**Recommendation:** Perform all registration writes within a single `get_connection()` context so they share one transaction.

---

### C-4. User Email Exposed to LLM in Chat Context
**File:** `/Users/rubertwolff/scratch/rivaflow/rivaflow/api/routes/chat.py`, lines 79-82

The `build_user_context()` function sends the user's full email address to the Ollama LLM:

```python
context_parts = [
    "USER PROFILE:",
    f"Name: {user['first_name']} {user['last_name']}",
    f"Email: {user['email']}",  # PII sent to LLM
```

**Impact:** PII (email) is sent to a potentially external LLM service, which could be a privacy/GDPR violation.
**Recommendation:** Remove email from the LLM context. The name alone is sufficient for personalization.

---

## HIGH Priority

### H-1. Duplicate `except ValueError` Clauses in Auth Routes
**File:** `/Users/rubertwolff/scratch/rivaflow/rivaflow/api/routes/auth.py`, lines 129-139

The `register()` function has overlapping exception handlers:

```python
except ValueError as e:          # Line 129 -- catches ValueError
    raise ValidationError(str(e))
except RivaFlowException:        # Line 132
    raise
except (ValueError, KeyError) as e:  # Line 134 -- ValueError already caught!
    ...
```

The second `ValueError` catch on line 134 is dead code because line 129 already catches it. Same pattern exists in `login()` (lines 158+166), `refresh_token()` (lines 189+198), and `reset_password()` (lines 332+336).

**Impact:** Dead exception handlers create confusion about which errors are handled where. If the first `ValueError` handler is removed in future, the second silently takes over with different behavior (500 instead of 400).
**Recommendation:** Remove the duplicate `ValueError` from the second catch clauses.

---

### H-2. `is_active = TRUE` / `is_active = 1` Inconsistency Across Repos
**Files:** Multiple repositories

- `user_repo.py` line 197: `WHERE is_active = TRUE` (PostgreSQL-only boolean literal)
- `user_repo.py` line 222: `WHERE is_active = TRUE`
- `whoop_connection_repo.py` line 131: `is_active = 1` (SQLite-compatible)
- `admin.py` line 1094: `WHERE is_active = ?` with param `(1,)` (numeric)

`TRUE` works in PostgreSQL but fails in SQLite. The `convert_query()` function does NOT convert boolean literals. All queries using `= TRUE` or `= FALSE` will fail on SQLite.

**Impact:** `UserRepository.list_all()` and `UserRepository.search()` will throw errors on SQLite.
**Recommendation:** Use parameterized `= ?` with `True`/`1` consistently, or use `convert_query()` and pass `1`/`0` as params.

---

### H-3. `social.py` User Search Loads ALL Users Into Memory
**File:** `/Users/rubertwolff/scratch/rivaflow/rivaflow/api/routes/social.py`, lines 386-412

The `search_users()` endpoint calls `UserRepository.list_all()` to fetch every active user, then filters in Python:

```python
all_users = UserRepository.list_all()
filtered_users = [user for user in all_users if ...]
```

This ignores the already-existing `UserRepository.search(query)` method which does the filtering in SQL.

**Impact:** O(N) memory for all users, O(N) iteration in Python. Will not scale.
**Recommendation:** Use `UserRepository.search(q)` which already does SQL `LIKE` filtering with `LIMIT`.

---

### H-4. `get_connection()` Auto-Commits on Context Exit -- Some Repos Also Manually Commit
**Files:** Multiple repositories including `streak_repo.py:37`, `notification_repo.py:58`, `checkin_repo.py:188`, `chat_session_repo.py:38`

The `get_connection()` context manager already calls `conn.commit()` on successful exit. However, many repositories also call `conn.commit()` manually inside the `with` block. This double-commit is mostly harmless but indicates confusion about the transaction model.

More importantly, `checkin_repo.py` line 188 calls `conn.commit()` inside `update_tomorrow_intention()`, which commits the current transaction prematurely -- any subsequent operations in the same `with` block would start a new implicit transaction.

**Impact:** Premature commits can cause partial write visibility and break atomicity guarantees.
**Recommendation:** Remove manual `conn.commit()` calls from repositories. Let the context manager handle commits.

---

### H-5. Dashboard Exception Handlers Swallow Real Errors as `ValidationError` (400)
**File:** `/Users/rubertwolff/scratch/rivaflow/rivaflow/api/routes/dashboard.py`, lines 139-140, 184-185, 255-256

```python
except Exception as e:
    raise ValidationError(f"Failed to load dashboard: {str(e)}")
```

All three dashboard endpoints catch `Exception` and re-raise as `ValidationError` (HTTP 400). This means database errors, connection timeouts, and programming bugs all get reported as client validation errors. The raw error message is also leaked to the client.

**Impact:** Server errors masquerade as 400s, making debugging difficult. Internal error details (potentially including stack trace info) leak to clients.
**Recommendation:** Use `HTTPException(status_code=500)` for unexpected errors. Use `handle_service_error()` to sanitize messages.

---

### H-6. Analytics Routes Leak Internal Error Details to Clients
**File:** `/Users/rubertwolff/scratch/rivaflow/rivaflow/api/routes/analytics.py`, many endpoints

Every analytics endpoint catches errors and returns the error message directly:

```python
raise HTTPException(
    status_code=500, detail=f"Analytics error: {type(e).__name__}: {str(e)}"
)
```

This pattern appears in ~20 endpoints in the analytics module. The `str(e)` can include SQL queries, table names, and column names.

**Impact:** Information leakage. Attackers can learn about database schema.
**Recommendation:** Use `handle_service_error()` from `error_handling.py` which logs details server-side but returns generic messages.

---

### H-7. `GoalsService()` Instantiated But Never Used
**File:** `/Users/rubertwolff/scratch/rivaflow/rivaflow/api/routes/dashboard.py`, line 222

```python
GoalsService()  # Instantiated but not assigned or used
```

**Impact:** Wasted object allocation. Likely a bug where the result was meant to be used.
**Recommendation:** Either remove the line or assign it to a variable and use it.

---

## MEDIUM Priority

### M-1. Missing Migration Numbers Create Confusion
**File:** `/Users/rubertwolff/scratch/rivaflow/rivaflow/db/database.py`, lines 428-505

The migration list in `_apply_migrations()` is missing numbers: 033, 046, 055, 056, 057, 068, 069, 070, 074. Some of these exist as files on disk (e.g., `046_social_features_comprehensive_pg.sql`, `055_add_missing_indexes.sql`, `068_migrate_techniques_to_glossary.sql`). They have corresponding `_pg.sql` variants on disk but are not in the hardcoded migration list.

Additionally, there are duplicate-numbered migration files on disk (e.g., `024_add_activity_photos.sql` and `024_add_activity_photos_pg.sql`, `041_create_notifications.sql` and `041_create_notifications_pg.sql`). The `_pg.sql` variants appear to be PostgreSQL-specific but are not referenced in the migration list.

**Impact:** Missing migrations could mean schema differences between SQLite and PostgreSQL deployments. The PG-specific migration files are orphaned.
**Recommendation:** Audit which PG-specific migrations have already been applied via `migrate.py` and document the separation. Consider consolidating the dual migration system.

---

### M-2. `_row_to_dict` Type Hint References `sqlite3.Row` Even for PostgreSQL
**Files:** Multiple repositories (`session_repo.py:453`, `user_repo.py:274`, `profile_repo.py:233`, `readiness_repo.py:176`, `friend_repo.py:201`, `glossary_repo.py:347`)

All `_row_to_dict` methods have type hints `row: sqlite3.Row` even though they also handle PostgreSQL `RealDictRow`. Many files import `sqlite3` solely for this type hint.

**Impact:** Misleading type annotations. Static analysis tools will flag PostgreSQL dict rows as type errors.
**Recommendation:** Use `Any` or create a `DatabaseRow = Union[sqlite3.Row, "RealDictRow"]` type alias.

---

### M-3. `convert_query()` Naively Replaces ALL `?` Characters
**File:** `/Users/rubertwolff/scratch/rivaflow/rivaflow/db/database.py`, lines 35-38

```python
def convert_query(query: str) -> str:
    if get_db_type() == "postgresql":
        return query.replace("?", "%s")
    return query
```

This replaces `?` inside string literals too. A query like `WHERE name LIKE '?%'` would become `WHERE name LIKE '%s%'`. While no current queries seem affected, this is fragile.

**Impact:** Potential SQL corruption if any query contains `?` in string literals.
**Recommendation:** Use a regex that skips `?` inside quoted strings, or use a proper SQL parameter translation library.

---

### M-4. N+1 Query Pattern in WHOOP Zones Batch Endpoint
**File:** `/Users/rubertwolff/scratch/rivaflow/rivaflow/api/routes/integrations.py`, lines 452-477

The `get_zones_batch()` endpoint issues one `WhoopWorkoutCacheRepository.get_by_session_id()` query per session ID, up to 50:

```python
for sid in ids:
    wo = WhoopWorkoutCacheRepository.get_by_session_id(sid)
```

**Impact:** Up to 50 separate database queries per request.
**Recommendation:** Add a batch method like `get_by_session_ids(ids: list[int])` using `WHERE session_id IN (...)`.

---

### M-5. N+1 Query Pattern in WHOOP Weekly Zones
**File:** `/Users/rubertwolff/scratch/rivaflow/rivaflow/api/routes/integrations.py`, lines 517-530

Similar to M-4, iterates over sessions and queries workouts one at a time:

```python
for s in sessions:
    wo = WhoopWorkoutCacheRepository.get_by_session_id(s["id"])
```

**Impact:** One query per session in the week (up to 14+ queries).
**Recommendation:** Batch the workout cache lookups.

---

### M-6. `get_session_with_details()` Has N+1 for Social Data
**File:** `/Users/rubertwolff/scratch/rivaflow/rivaflow/core/services/session_service.py`, lines 384-419

This method loads likes, comments, like count, comment count, and has_liked in 5 separate queries for each session.

**Impact:** 5+ queries per session detail load on top of the session query itself.
**Recommendation:** Consider combining likes/comments into a single JOIN query or at minimum a batch operation.

---

### M-7. Social Followers/Following Pagination Done In-Memory
**File:** `/Users/rubertwolff/scratch/rivaflow/rivaflow/api/routes/social.py`, lines 124-147

Both `get_followers()` and `get_following()` fetch ALL results, then slice in Python:

```python
all_followers = SocialService.get_followers(current_user["id"])
total = len(all_followers)
followers = all_followers[offset : offset + limit]
```

**Impact:** All followers are loaded into memory even if only requesting page 2 of 10.
**Recommendation:** Pass `limit` and `offset` to the repository/service layer.

---

### M-8. `get_last_n_sessions_by_type()` Return Type Annotation Is Wrong
**File:** `/Users/rubertwolff/scratch/rivaflow/rivaflow/db/repositories/session_repo.py`, line 411

```python
def get_last_n_sessions_by_type(user_id: int, n: int = 5) -> dict[str, list[str]]:
```

The method actually returns `list[str]` (a flat list of class type strings), not `dict[str, list[str]]`.

**Impact:** Misleading type annotation; IDE/mypy will give wrong autocomplete.
**Recommendation:** Change return type to `list[str]`.

---

### M-9. Grapple Chat Exposes Internal Error Messages to Clients
**File:** `/Users/rubertwolff/scratch/rivaflow/rivaflow/api/routes/grapple.py`, lines 233-234, 246-248, 257-259

```python
detail=f"Failed to create chat session: {type(e).__name__}: {e}",
detail=f"Failed to store message: {type(e).__name__}: {e}",
detail=f"Failed to build context: {type(e).__name__}: {e}",
```

**Impact:** Internal exception types and messages are exposed in API responses.
**Recommendation:** Return generic error messages; log details server-side.

---

### M-10. `admin.py` Route Directly Writes SQL Instead of Using Repository
**File:** `/Users/rubertwolff/scratch/rivaflow/rivaflow/api/routes/admin.py`, many locations (lines 398-467, 494-548, 559-615, etc.)

The admin routes bypass the repository layer and write raw SQL queries directly against `get_connection()`. This violates the routes -> services -> repos separation of concerns.

**Impact:** Business logic scattered across route handlers; harder to test and maintain. SQL compatibility issues may differ from repos.
**Recommendation:** Create `AdminService` or use existing repositories for data access.

---

### M-11. `admin.py` Uses Deprecated `gym_data.dict()` Instead of `model_dump()`
**File:** `/Users/rubertwolff/scratch/rivaflow/rivaflow/api/routes/admin.py`, line 195

```python
update_data = {k: v for k, v in gym_data.dict().items() if v is not None}
```

Pydantic v2 deprecated `.dict()` in favor of `.model_dump()`.

**Impact:** Deprecation warning; will break in Pydantic v3.
**Recommendation:** Use `gym_data.model_dump(exclude_none=True)`.

---

### M-12. Profile GET Returns Hardcoded `id: 1` for Missing Profile
**File:** `/Users/rubertwolff/scratch/rivaflow/rivaflow/api/routes/profile.py`, lines 127-139

```python
if not profile:
    return {
        "id": 1,  # Hardcoded
        ...
    }
```

**Impact:** All users without profiles get `id: 1`, which is incorrect and could cause frontend confusion.
**Recommendation:** Return `null`/`None` or use the actual user_id.

---

## LOW Priority

### L-1. Unused `import threading` and `import time` in admin.py
**File:** `/Users/rubertwolff/scratch/rivaflow/rivaflow/api/routes/admin.py`, lines 4-5

`threading` and `time` are imported at module level but `time` is only used inside `_send_broadcast_background()` and `threading` is used only for `threading.Thread`. These are fine technically but could be lazy imports.

---

### L-2. Unused Imports in Various Files
**File:** `/Users/rubertwolff/scratch/rivaflow/rivaflow/db/repositories/glossary_repo.py`, line 5

`timedelta` and `date` are imported from `datetime` but `date` and `timedelta` are only used in `get_stale()`. Minor.

**File:** `/Users/rubertwolff/scratch/rivaflow/rivaflow/api/routes/sessions.py`, lines 4, 14

`asyncio` is imported at module level but only used in one background task helper. `Response` is imported but only used once.

---

### L-3. `_reset_postgresql_sequences` Catches Too-Broad OS Errors
**File:** `/Users/rubertwolff/scratch/rivaflow/rivaflow/db/database.py`, lines 308-312

```python
except (OSError, ConnectionError) as e:
    conn.rollback()
    ...
    pass  # Redundant pass after logger call
```

`OSError` is very broad. The actual expected errors would be `psycopg2.Error` or `psycopg2.ProgrammingError`.

**Impact:** Could mask genuine OS-level errors.
**Recommendation:** Catch `Exception` or specifically `psycopg2.Error`.

---

### L-4. `readiness.py` Weight Endpoint Uses `dict` Instead of Pydantic Model
**File:** `/Users/rubertwolff/scratch/rivaflow/rivaflow/api/routes/readiness.py`, line 124

```python
def log_weight_only(request: Request, data: dict, ...):
```

All other endpoints use Pydantic models for request validation. Using raw `dict` bypasses FastAPI's automatic validation and OpenAPI docs generation.

**Impact:** No automatic input validation; manual `try/except KeyError` needed.
**Recommendation:** Create a `WeightLogRequest(BaseModel)` with `weight_kg: float` and `check_date: date | None`.

---

### L-5. `chat.py` Uses `total_sessions` Before It May Be Defined
**File:** `/Users/rubertwolff/scratch/rivaflow/rivaflow/api/routes/chat.py`, lines 84-86

```python
if total_sessions > 0:
    context_parts.append(f"Total training time: {total_duration} minutes")
```

`total_sessions`, `total_duration`, `total_rolls`, `avg_intensity`, `gyms`, `all_techniques` are all defined inside the `if total_sessions > 0` block on line 64. If `total_sessions == 0`, the variables are defined in the outer scope. But `total_sessions` is first used on line 87 as `context_parts.append(...)`, which references `total_sessions` defined on line 63. This is fine, but the `gyms` and `all_techniques` variables are only defined in the `if total_sessions > 0` block and referenced nowhere outside it, which is correct but fragile.

---

### L-6. Inconsistent Service Instantiation Pattern
**Files:** Multiple route files

Some route files instantiate services at module level:
- `sessions.py`: `service = SessionService()` (module-level singleton)
- `analytics.py`: `service = AnalyticsService()` (module-level singleton)
- `integrations.py`: `service = WhoopService()` (module-level singleton)

Others instantiate per-request:
- `auth.py`: `service = AuthService()` inside each route handler
- `dashboard.py`: `AnalyticsService()` inside cached helper

Module-level instantiation means these services share state across requests (which is fine for stateless services but could cause issues if services ever hold request-scoped state).

**Impact:** Inconsistency makes it harder to reason about service lifecycle.
**Recommendation:** Pick one pattern and use it consistently. Module-level is fine for stateless services.

---

### L-7. Some Routes Missing Rate Limiting
**Files:** Several route files

These endpoints have no rate limiting:
- `social.py`: `get_followers()`, `get_following()`, `check_following()`, `get_activity_likes()`, `get_activity_comments()`, several friend request endpoints
- `sessions.py`: `get_session()`, `get_sessions_by_range()`, `get_autocomplete_data()`, `get_session_insights()`, `get_session_with_rolls()`

While the slowapi limiter is initialized in these modules, not all endpoints use the `@limiter.limit()` decorator.

**Impact:** Unprotected endpoints could be abused for scraping or DoS.
**Recommendation:** Add rate limiting to all endpoints, even generous limits like `120/minute`.

---

### L-8. `admin.py` Broadcast Uses `is_active = ?` with `(1,)` Instead of `(True,)`
**File:** `/Users/rubertwolff/scratch/rivaflow/rivaflow/api/routes/admin.py`, line 1094

```python
cursor.execute(convert_query("... WHERE is_active = ?"), (1,))
```

PostgreSQL with `boolean` column type expects `True`/`False`, not `1`/`0`. This works by accident because `1` is truthy in PG, but `is_active = 1` is not semantically correct for a boolean column.

**Impact:** Works but semantically wrong; could break with stricter PG type checking.
**Recommendation:** Use `(True,)` as the parameter.

---

### L-9. Glossary `list_all()` Hardcodes `gi_applicable = 1` Instead of Using Boolean
**File:** `/Users/rubertwolff/scratch/rivaflow/rivaflow/db/repositories/glossary_repo.py`, lines 37-40

```python
if gi_only:
    query += " AND gi_applicable = 1"
if nogi_only:
    query += " AND nogi_applicable = 1"
```

**Impact:** Works on both SQLite and PG but inconsistent with `= TRUE` pattern used elsewhere.
**Recommendation:** Use parameterized query with `= ?` and `(True,)`.

---

### L-10. Missing Index Opportunities

Several queries filter on columns that may lack indexes:
- `sessions.session_date` -- used in range queries, BETWEEN, ORDER BY
- `daily_checkins.check_date + checkin_slot` -- queried together frequently
- `readiness.check_date` -- used in range queries
- `whoop_workout_cache.session_id` -- used in lookups from integrations

**Impact:** Slower queries as data grows.
**Recommendation:** Verify indexes exist for these columns in the migration files. Migration `040_add_performance_indexes.sql` may cover some of these.

---

## Architecture Notes

### Positive Patterns Observed

1. **Consistent use of `convert_query()`** for SQL portability across repositories
2. **Proper parameterized queries** -- no string interpolation of user input into SQL
3. **Good `_row_to_dict()` pattern** -- centralized row conversion in each repository
4. **Field whitelisting on updates** -- repositories validate update field names against hardcoded sets, preventing SQL injection via dynamic column names
5. **`handle_service_error()`** utility properly separates server-side logging from client-facing messages (though underutilized)
6. **Rate limiting on sensitive endpoints** (auth, password reset)
7. **Proper HTTP status codes** on auth failures (401), missing resources (404), created resources (201)
8. **Background tasks** for non-critical operations (streak recording, milestone checks, AI insights)
9. **Audit logging** on admin operations
10. **Connection pooling** for PostgreSQL with `ThreadedConnectionPool`

### Areas for Architectural Improvement

1. **Transaction boundaries** are the single biggest architectural concern. The one-connection-per-method pattern makes multi-table operations non-atomic (C-1, C-3).
2. **Error handling** should be standardized -- the codebase uses 4 different patterns: `RivaFlowException` subclasses, bare `HTTPException`, `handle_service_error()`, and raw `except Exception` that leaks details.
3. **Admin routes bypass the service/repository layers** and contain raw SQL, violating the clean architecture pattern used elsewhere.
