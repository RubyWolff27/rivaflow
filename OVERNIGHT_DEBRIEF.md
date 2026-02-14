# RivaFlow Overnight Codebase Review -- Debrief Report

**Date:** 2026-02-11
**Reviewed by:** 6 automated review agents + 1 orchestration agent
**Scope:** Full codebase -- backend, frontend, testing, DevOps, security, product/UX

---

## 1. Executive Summary

- **Overall health is solid for a beta product.** The codebase demonstrates good security fundamentals (bcrypt, parameterized SQL, CORS whitelisting, rate limiting, admin audit logging) and a well-designed architecture (routes -> services -> repos separation, dual-DB portability, lazy-loaded frontend).
- **Mobile responsiveness is the single biggest user-facing gap.** 14+ grid layouts use fixed column counts without responsive breakpoints, causing content to be crushed or inaccessible on phones (the primary device for a fitness app).
- **Error information leakage is the top security concern.** 27+ API endpoints return internal exception types, class names, and error messages directly to clients, aiding potential attackers in understanding the stack.
- **Test coverage is deep but narrow.** The tests that exist are well-written behavioral tests. But only ~30% of route modules, ~11% of frontend pages, and 0% of frontend components have any test coverage.
- **Transaction boundaries are the primary architectural concern.** Multi-table operations (session delete, user registration) use separate database connections for related writes, creating data integrity risks.

---

## 2. Fixes Applied

All fixes passed: `black` (243 files unchanged), `ruff` (all checks passed), `tsc --noEmit` (clean), `pytest` (310 passed, 1 skipped, 1 xfailed, 1 xpassed).

### Backend Fixes

| # | File | What Was Wrong | What Was Done |
|---|------|---------------|---------------|
| 1 | `rivaflow/rivaflow/db/repositories/user_repo.py:197` | `WHERE is_active = TRUE` -- PostgreSQL boolean literal fails on SQLite | Changed to parameterized `WHERE is_active = ?` with `(1,)` |
| 2 | `rivaflow/rivaflow/db/repositories/user_repo.py:222` | Same `is_active = TRUE` issue in `search()` | Changed to parameterized `WHERE is_active = ?` with `(1, ...)` |
| 3 | `rivaflow/rivaflow/api/routes/auth.py:134` | Duplicate `ValueError` in except clause (dead code) in `register()` | Changed `(ValueError, KeyError)` to `KeyError` only |
| 4 | `rivaflow/rivaflow/api/routes/auth.py:166` | Duplicate `ValueError` in except clause in `login()` | Changed `(ValueError, KeyError)` to `KeyError` only |
| 5 | `rivaflow/rivaflow/api/routes/auth.py:198` | Duplicate `ValueError` in except clause in `refresh_token()` | Changed `(ValueError, KeyError)` to `KeyError` only |
| 6 | `rivaflow/rivaflow/api/routes/auth.py:336` | Duplicate `ValueError` in except clause in `reset_password()` | Changed `(ValueError, KeyError)` to `KeyError` only |
| 7 | `rivaflow/rivaflow/api/routes/dashboard.py:222` | `GoalsService()` instantiated but never assigned or used | Removed the dead line |
| 8 | `rivaflow/rivaflow/api/routes/dashboard.py:140,186,256` | Error responses leak `str(e)` to clients | Replaced with generic messages; added `logger.error()` for server-side logging; added `import logging` and `logger` |
| 9 | `rivaflow/rivaflow/api/routes/analytics.py` (27 locations) | All error responses included `f"Analytics error: {type(e).__name__}: {str(e)}"` | Replaced all 27 occurrences with generic `"An error occurred while processing analytics"` |
| 10 | `rivaflow/rivaflow/api/routes/grapple.py:170,233,247,259,275,548,682,756` | Error responses leak exception types/messages | Replaced with generic messages; added server-side logging for session extraction and technique QA errors |
| 11 | `rivaflow/rivaflow/api/routes/grapple.py:165,678` | `except Exception as e:` with unused `e` (ruff F841) | Changed to `except Exception:` |
| 12 | `rivaflow/rivaflow/api/routes/admin.py:388` | Gym merge error leaks `str(e)` | Replaced with generic message + server-side logging |

### Frontend Fixes

| # | File | What Was Wrong | What Was Done |
|---|------|---------------|---------------|
| 13 | `Login.tsx:30` | `var(--background)` does not exist in CSS tokens; should be `var(--bg)` | Replaced `var(--background)` with `var(--bg)` |
| 14 | `Register.tsx:50` | Same `var(--background)` issue | Replaced with `var(--bg)` |
| 15 | `ForgotPassword.tsx:29,59` | Same `var(--background)` issue (2 occurrences) | Replaced with `var(--bg)` |
| 16 | `ResetPassword.tsx:61,91` | Same `var(--background)` issue (2 occurrences) | Replaced with `var(--bg)` |
| 17 | `Waitlist.tsx:49,90` | Same `var(--background)` issue (2 occurrences) | Replaced with `var(--bg)` |
| 18 | `ErrorBoundary.tsx:68-119` | Used non-existent Tailwind classes (`bg-surface`, `text-text`, `bg-card`, `btn btn-primary`, etc.) and linked to `/feedback` (route doesn't exist) | Rewrote to use inline CSS variables (`var(--bg)`, `var(--surface)`, etc.), `rounded-[14px]`, and changed link to `/contact` |
| 19 | `ToastContext.tsx:66` | Toast container at `bottom-4` overlaps mobile bottom nav | Changed to `bottom-20 md:bottom-4` |
| 20 | `Grapple.tsx:762` | `100vh` unreliable on mobile (dynamic browser chrome) | Changed to `100dvh` |
| 21 | `LogSession.tsx:1503-1584` | Fight dynamics +/- buttons `w-9 h-9` (36px) below 44px touch target | Changed all 8 buttons to `w-11 h-11` (44px) |
| 22 | `App.tsx:118` | No 404 catch-all route; navigating to unknown URLs shows blank content | Added `<Route path="*" element={<NotFound />} />` inside nested Routes |
| 23 | `NotFound.tsx` (new file) | Page did not exist | Created minimal 404 page with dashboard link |
| 24 | `Reports.tsx:347` | Tab bar overflow on mobile (no horizontal scroll) | Added `overflow-x-auto scrollbar-hide` + `flex-shrink-0` on tabs |
| 25 | `Reports.tsx:578` | `grid-cols-3` time-of-day stats crushed on mobile | Changed to `grid-cols-1 sm:grid-cols-3` |
| 26 | `Reports.tsx:685` | `grid-cols-5` HR zone data crushed on mobile | Changed to `grid-cols-3 sm:grid-cols-5` |
| 27 | `Reports.tsx:413` | Custom date range `flex` overflows on mobile | Added `flex-wrap` and tighter gap (`gap-2 sm:gap-4`) |
| 28 | `Reports.tsx:380` | Quick range buttons could overflow on narrow screens | Added `flex-wrap` |
| 29 | `Friends.tsx:265` | `grid-cols-3` form inputs cramped on mobile | Changed to `grid-cols-1 sm:grid-cols-3` |
| 30 | `Profile.tsx:1021` | `grid-cols-3` weekly goals inputs cramped on mobile | Changed to `grid-cols-1 sm:grid-cols-3` |
| 31 | `MyGame.tsx:238` | `grid-cols-5` belt selector untappable on mobile | Changed to `grid-cols-3 sm:grid-cols-5` |
| 32 | `WhoopAnalyticsTab.tsx:90` | `grid-cols-3` recovery zones crushed on mobile | Changed to `grid-cols-1 sm:grid-cols-3` |
| 33 | `WhoopAnalyticsTab.tsx:190` | `grid-cols-3` sleep stats crushed on mobile | Changed to `grid-cols-1 sm:grid-cols-3` |
| 34 | `WhoopAnalyticsTab.tsx:219` | `grid-cols-3` cardio stats crushed on mobile | Changed to `grid-cols-1 sm:grid-cols-3` |
| 35 | `WhoopAnalyticsTab.tsx:326` | `grid-cols-4` zone breakdown crushed on mobile | Changed to `grid-cols-2 sm:grid-cols-4` |

All frontend changes synced to `web/` via `rsync -a --delete rivaflow/web/ web/`.

---

## 3. Critical Items Requiring Human Decision

Ranked by severity and impact.

### P0 -- Fix Before Next Deploy

**3.1 Webhook signature bypass when secret missing** (Security HIGH)
- File: `rivaflow/rivaflow/api/routes/webhooks.py:73-82`
- When `WHOOP_CLIENT_SECRET` is not set, the webhook endpoint skips ALL signature verification and processes any payload.
- **Risk:** If the env var is accidentally removed, attackers can send forged webhook payloads to create fake sessions or manipulate user data.
- **Recommended fix:** Reject all requests with HTTP 503 when the secret is missing. Never fail open.

**3.2 Session delete cross-connection transaction bug** (Data integrity CRITICAL)
- File: `rivaflow/rivaflow/db/repositories/session_repo.py:432-450`
- `delete()` opens one connection, then calls `SessionRollRepository.delete_by_session()` and `SessionTechniqueRepository.delete_by_session()` which each open separate connections. If the parent DELETE fails, child records are already committed and gone.
- **Recommended fix:** Pass the existing connection/cursor to child repository methods, or perform all deletes in a single `with get_connection()` block.

**3.3 Auth registration non-atomic multi-transaction writes** (Data integrity CRITICAL)
- File: `rivaflow/rivaflow/core/services/auth_service.py:95-176`
- User creation, profile creation, and streak initialization each happen in separate `get_connection()` contexts. If the app crashes mid-registration, partial data persists.
- **Recommended fix:** Wrap all registration writes in a single `get_connection()` context.

**3.4 Database publicly accessible (empty ipAllowList)** (Security CRITICAL)
- File: `render.yaml:83`
- `ipAllowList: []` means the PostgreSQL database accepts connections from any IP.
- **Recommended fix:** Restrict `ipAllowList` to Render service IPs or use internal connection strings only.

### P1 -- Fix This Week

**3.5 Token refresh race condition** (Frontend CRITICAL)
- File: `rivaflow/web/src/api/client.ts:66-101`
- Multiple concurrent 401s each trigger their own `authApi.refresh()`, causing unnecessary logouts.
- **Recommended fix:** Implement a shared promise pattern for the refresh flow. ~20 line change.

**3.6 JWT tokens stored in localStorage** (Security HIGH)
- Files: `AuthContext.tsx:66-67`, `client.ts:28`
- Both access and refresh tokens in localStorage are accessible to any XSS.
- **Recommended fix:** Migrate refresh token to httpOnly cookie. Keep access token in memory only. This is an architectural change requiring backend cookie support.

**3.7 WHOOP zones batch IDOR** (Security MEDIUM)
- File: `rivaflow/rivaflow/api/routes/integrations.py:439-479`
- `WhoopWorkoutCacheRepository.get_by_session_id()` does not filter by `user_id`. Any authenticated user can probe arbitrary session IDs for WHOOP data.
- **Recommended fix:** Add `AND user_id = ?` to the query or verify session ownership in the route handler.

**3.8 User email sent to LLM** (Privacy MEDIUM)
- File: `rivaflow/rivaflow/api/routes/chat.py:79-82`
- The user's email is included in the LLM context. Name alone is sufficient for personalization.
- **Recommended fix:** Remove the email line from `build_user_context()`.

**3.9 `python-jose` is unmaintained with known CVEs** (Security CRITICAL)
- File: `rivaflow/requirements.txt:14`
- `python-jose==3.5.0` has not been updated since 2022. The `ecdsa` dependency has CVE-2024-23342.
- **Recommended fix:** Migrate to `PyJWT` (actively maintained).

### P2 -- Fix This Sprint

**3.10 Render auto-deploy not gated on CI tests** (DevOps HIGH)
- `render.yaml` has `autoDeploy: true` which deploys on every push to main, regardless of test results.
- **Recommended fix:** Set `autoDeploy: false` and trigger deploys via Render API after CI passes, or use GitHub branch protection.

**3.11 Dual migration path risks schema drift** (DevOps CRITICAL)
- Migrations run 3 times at startup from different entry points.
- **Recommended fix:** Pick one migration entry point and remove duplicates.

**3.12 Notification repository uses RETURNING without SQLite fallback** (Backend CRITICAL)
- File: `rivaflow/rivaflow/db/repositories/notification_repo.py:37-41`
- `RETURNING` clause is PostgreSQL-only.
- **Recommended fix:** Use `execute_insert()` + separate SELECT, or add SQLite fallback.

**3.13 Grapple rate limiter fails open** (Security MEDIUM)
- File: `rivaflow/rivaflow/api/routes/grapple.py:190-193`
- When rate limit storage fails, users get unlimited LLM access, risking runaway costs.
- **Recommended fix:** Add in-memory fallback or fail closed with alerting.

---

## 4. Consolidated Priority Matrix

All issues from all 6 reviews, deduplicated and ranked.

### P0 -- Fix Before Next Deploy

| ID | Source | Issue | Type |
|----|--------|-------|------|
| P0-1 | Security 10.1 | Webhook signature bypass when secret missing | Security |
| P0-2 | Backend C-1 | Session delete cross-connection transaction bug | Data integrity |
| P0-3 | Backend C-3 | Auth registration non-atomic writes | Data integrity |
| P0-4 | DevOps C2 | Database publicly accessible (empty ipAllowList) | Security |
| P0-5 | Backend C-2 | Notification repo `RETURNING` breaks SQLite | Compatibility |
| P0-6 | Backend C-4 | User email sent to LLM | Privacy |
| P0-7 | Security 3.1 | **[FIXED]** Error details leaked in production responses (27+ analytics, grapple, dashboard, admin endpoints) | Security |

### P1 -- Fix This Week

| ID | Source | Issue | Type |
|----|--------|-------|------|
| P1-1 | Frontend C-1 | Token refresh race condition | UX/Auth |
| P1-2 | Security 1.1 | JWT tokens in localStorage | Security |
| P1-3 | Security 1.3 | WHOOP zones batch IDOR (no user_id filter) | Security |
| P1-4 | DevOps C3 | `python-jose` unmaintained with CVE | Security |
| P1-5 | DevOps H1 | Render auto-deploy not gated on CI | DevOps |
| P1-6 | DevOps C4 | Dual migration path with 3x startup runs | DevOps |
| P1-7 | Backend H-2 | **[FIXED]** `is_active = TRUE` SQLite incompatibility | Compatibility |
| P1-8 | Backend H-4 | Double-commit / premature commit in repos | Data integrity |
| P1-9 | Backend H-3 | Social user search loads ALL users into memory | Performance |
| P1-10 | Security 5.2 | CSP/HSTS/security headers missing from frontend static site | Security |

### P2 -- Fix This Sprint

| ID | Source | Issue | Type |
|----|--------|-------|------|
| P2-1 | Security 3.4 | Grapple rate limiter fails open | Security |
| P2-2 | Security 3.5 | Weak password requirements (only length check) | Security |
| P2-3 | Security 1.2 | WHOOP OAuth callback URL parameter not sanitized | Security |
| P2-4 | DevOps H2 | Single uvicorn worker, no gunicorn | Performance |
| P2-5 | DevOps H3 | Dependency version drift across 3 manifests | Maintenance |
| P2-6 | DevOps H5 | `@app.on_event` deprecated, use lifespan | Maintenance |
| P2-7 | DevOps H6 | `datetime.utcnow()` deprecated throughout codebase | Maintenance |
| P2-8 | DevOps H7 | APScheduler uses SQLite date functions in PG context | Bug |
| P2-9 | Backend H-5 | Dashboard exception handlers swallow as 400 (ValidationError) | Bug |
| P2-10 | Frontend C-2 | 26 `useState<any>` instances eliminate type safety | Type safety |
| P2-11 | Frontend H-1 | Oversized components (LogSession 1755 lines, Profile 1587) | Maintainability |
| P2-12 | Product C-2 | Grapple chat history inaccessible on mobile (sidebar hidden) | UX |
| P2-13 | Product H-2 | **[PARTIALLY FIXED]** ~20 hardcoded Tailwind colors break dark mode | UX |
| P2-14 | Frontend H-4 | FeedbackModal type mismatch ('general' not in union) | Bug |
| P2-15 | Backend M-4/M-5 | N+1 query in WHOOP zones batch + weekly zones | Performance |
| P2-16 | Backend M-6 | N+1 query in session details (5 social queries per session) | Performance |

### P3 -- Backlog

| ID | Source | Issue | Type |
|----|--------|-------|------|
| P3-1 | Backend M-1 | Missing migration numbers / PG-specific orphaned files | Maintenance |
| P3-2 | Backend M-2 | `_row_to_dict` type hints reference `sqlite3.Row` for PG | Type safety |
| P3-3 | Backend M-3 | `convert_query()` naively replaces ALL `?` characters | Bug risk |
| P3-4 | Backend M-7 | Social pagination done in-memory | Performance |
| P3-5 | Backend M-8 | Wrong return type on `get_last_n_sessions_by_type()` | Type safety |
| P3-6 | Backend M-10 | Admin routes bypass service/repo layer with raw SQL | Architecture |
| P3-7 | Backend M-11 | Admin uses deprecated `.dict()` instead of `.model_dump()` | Maintenance |
| P3-8 | Backend M-12 | Profile GET returns hardcoded `id: 1` for missing profile | Bug |
| P3-9 | Frontend M-2/M-3 | Toast `setTimeout` without cleanup in context + component | Memory leak |
| P3-10 | Frontend M-4 | Sessions page loads ALL records (`limit=1000`) | Performance |
| P3-11 | Frontend M-5 | Profile.tsx duplicate data loading logic | Maintenance |
| P3-12 | Frontend M-6 | Sessions.tsx missing useEffect dependency | Bug risk |
| P3-13 | Frontend M-9 | Clickable `<div>` without keyboard/a11y support | Accessibility |
| P3-14 | Frontend M-10 | Limited `tabIndex` usage (only 1 instance) | Accessibility |
| P3-15 | Product M-5 | Grapple delete button only visible on hover (no touch) | UX |
| P3-16 | Product M-6 | Friends belt color classes break in dark mode | UX |
| P3-17 | Product L-1 | `console.log` left in SessionDetail.tsx | Polish |
| P3-18 | Product L-4 | Page title "Analytics" vs nav label "Progress" mismatch | UX |
| P3-19 | DevOps M1 | No Codecov token configured | CI |
| P3-20 | DevOps M4 | No structured/JSON logging for production | Observability |
| P3-21 | DevOps M7 | Connection pool maxconn=40 may exceed Render starter limit | Reliability |
| P3-22 | DevOps M9 | Smoke test does not fail workflow on DB health check failure | CI |
| P3-23 | DevOps M10 | TruffleHog pinned to `@main` (unstable) | CI |
| P3-24 | Security 3.3 | Rate limiting inconsistencies on write endpoints | Security |
| P3-25 | Backend L-7 | Some routes missing rate limiting | Security |
| P3-26 | Backend L-10 | Missing index opportunities on frequently queried columns | Performance |
| P3-27 | DevOps L1 | Dual `web/` directory sync is fragile (partial diff check) | DevOps |
| P3-28 | DevOps L4 | Hardcoded API version "0.2.0" vs pyproject.toml "0.5.0" | Maintenance |
| P3-29 | Testing | Only 5/47 frontend pages tested, 0/70 components tested | Coverage |
| P3-30 | Testing | Auth/Session/Readiness/Profile routes have zero route-level tests | Coverage |
| P3-31 | Testing | 17 WHOOP integration endpoints with zero route tests | Coverage |

---

## 5. Quick Wins Remaining

Safe fixes identified but not applied (to keep the change set small and reviewable):

| # | File | Description | Effort |
|---|------|-------------|--------|
| 1 | `Sessions.tsx:242` | `grid-cols-3` session stats -- add `grid-cols-1 sm:grid-cols-3` | 1 min |
| 2 | `Dashboard.tsx:67` | `grid-cols-3` Grapple buttons -- add `py-4` for taller touch targets | 1 min |
| 3 | `SessionDetail.tsx:525` | `grid-cols-3` roll stats -- add responsive breakpoint | 1 min |
| 4 | `CoachSettings.tsx:507` | `grid-cols-3` coach preferences -- add responsive breakpoint | 1 min |
| 5 | `WhoopMatchModal.tsx:88` | `grid-cols-3` match stats -- add responsive breakpoint | 1 min |
| 6 | `AdminGrapple.tsx:297` | `grid-cols-3` grapple stats -- add responsive breakpoint | 1 min |
| 7 | `SessionDetail.tsx:68,71` | Remove `console.log` debug statements | 1 min |
| 8 | `admin.py:195` | Replace `.dict()` with `.model_dump(exclude_none=True)` | 1 min |
| 9 | `profile.py:127-139` | Replace hardcoded `"id": 1` with `user_id` for missing profile | 1 min |
| 10 | `chat.py:82` | Remove user email from LLM context | 1 min |
| 11 | Multiple repos | Remove manual `conn.commit()` calls (let context manager handle) | 5 min |
| 12 | `Reports.tsx:312-336` | Add `flex-wrap gap-3` to page header for mobile | 2 min |
| 13 | `Friends.tsx:10-16` | Add `dark:` variants to belt color badge classes | 5 min |
| 14 | `ResetPassword.tsx:67` | Replace `bg-green-50 border-green-200` with CSS vars for dark mode | 1 min |
| 15 | `Techniques.tsx:78` | Replace `bg-yellow-50 border-yellow-200` with CSS vars | 1 min |

---

## 6. Technical Debt Summary

### Theme 1: Mobile Responsiveness (HIGH impact)
14+ grid layouts used fixed `grid-cols-3/4/5` without responsive breakpoints. 9 fixed in this round; 6 remaining. The app is a BJJ training tracker primarily used on phones -- mobile must be first-class.

### Theme 2: Error Information Leakage (HIGH impact)
27 analytics endpoints, 8 grapple endpoints, 3 dashboard endpoints, and 1 admin endpoint all leaked internal error details (`type(e).__name__`, `str(e)`) to clients. All fixed in this round. The pattern should be enforced via a linting rule or code review checklist.

### Theme 3: Transaction Boundaries (CRITICAL architectural)
The one-connection-per-method pattern makes multi-table operations non-atomic. Session deletion, user registration, and potentially other multi-step writes are affected. This is the single biggest data integrity risk.

### Theme 4: Type Safety Gaps (MEDIUM)
Frontend: 26 `useState<any>`, 15 `as any` casts, 6 `catch (error: any)`. Backend: `_row_to_dict` hints reference `sqlite3.Row` even for PG. These gaps eliminate compile-time safety for the most data-heavy parts of the app.

### Theme 5: Test Coverage Breadth (HIGH)
Tests that exist are well-written. But: ~70% of route modules have zero tests, ~89% of frontend pages are untested, 100% of frontend components are untested, and no tests exist for admin, notifications, photos, groups, events, or checkins.

### Theme 6: SQLite/PostgreSQL Compatibility (MEDIUM)
Several patterns work on PG but fail on SQLite: `is_active = TRUE` (fixed), `RETURNING` clause, `date('now', ...)` in scheduler, boolean literal usage inconsistency. Local dev uses SQLite, so these cause developer friction.

### Theme 7: Deprecated APIs (LOW-MEDIUM)
`datetime.utcnow()` (~40 occurrences), `@app.on_event` (startup/shutdown), `.dict()` instead of `.model_dump()`. These work today but will break in future Python/FastAPI/Pydantic versions.

### Theme 8: Component Size (MEDIUM)
Three frontend pages exceed 1000 lines: `LogSession.tsx` (1755), `Profile.tsx` (1587), `Reports.tsx` (1120). These need decomposition for maintainability and testability.

---

## Files Modified (not committed)

**Backend (6 files):**
- `rivaflow/rivaflow/api/routes/admin.py`
- `rivaflow/rivaflow/api/routes/analytics.py`
- `rivaflow/rivaflow/api/routes/auth.py`
- `rivaflow/rivaflow/api/routes/dashboard.py`
- `rivaflow/rivaflow/api/routes/grapple.py`
- `rivaflow/rivaflow/db/repositories/user_repo.py`

**Frontend (16 files, all synced to `web/`):**
- `rivaflow/web/src/App.tsx`
- `rivaflow/web/src/components/ErrorBoundary.tsx`
- `rivaflow/web/src/components/analytics/WhoopAnalyticsTab.tsx`
- `rivaflow/web/src/contexts/ToastContext.tsx`
- `rivaflow/web/src/pages/ForgotPassword.tsx`
- `rivaflow/web/src/pages/Friends.tsx`
- `rivaflow/web/src/pages/Grapple.tsx`
- `rivaflow/web/src/pages/LogSession.tsx`
- `rivaflow/web/src/pages/Login.tsx`
- `rivaflow/web/src/pages/MyGame.tsx`
- `rivaflow/web/src/pages/NotFound.tsx` (new)
- `rivaflow/web/src/pages/Profile.tsx`
- `rivaflow/web/src/pages/Register.tsx`
- `rivaflow/web/src/pages/Reports.tsx`
- `rivaflow/web/src/pages/ResetPassword.tsx`
- `rivaflow/web/src/pages/Waitlist.tsx`

**Verification results:**
- `black rivaflow/ tests/` -- 243 files unchanged (no formatting needed)
- `ruff check rivaflow/ tests/ --ignore=C901,N802,N818,UP042,F823` -- All checks passed
- `npx tsc --noEmit` -- Clean (no errors)
- `python -m pytest tests/ -x -q` -- 310 passed, 1 skipped, 1 xfailed, 1 xpassed
- `rsync -a --delete rivaflow/web/ web/` -- Synced successfully
