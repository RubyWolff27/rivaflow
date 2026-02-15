# RivaFlow Audit Fix Plan — All Waves

**Created:** 2026-02-15
**Goal:** Address all findings from the full-stack audit in a single session, organized by dependency order.
**Reference:** `RIVAFLOW_REVIEW_REPORT.md` for full finding details.

---

## Pre-Flight Checklist
- [ ] Ensure on `main` branch, clean working tree
- [ ] Run existing tests to confirm green baseline: `cd /Users/rubertwolff/scratch && pytest tests/ -x -q`
- [ ] Run frontend build to confirm clean: `cd rivaflow/web && npm run build`

---

## WAVE 1: Critical Safety (No code refactoring — just fixes)

### 1.1 Move inner tests to CI
- Add `rivaflow/tests/` to pytest collection in `.github/workflows/test.yml`
- Verify no fixture conflicts between `tests/conftest.py` and `rivaflow/tests/`
- **Files:** `.github/workflows/test.yml`

### 1.2 Fix tier_check.py getattr → .get()
- Lines 39, 82, 135, 173: change `getattr(current_user, "subscription_tier", "free")` → `current_user.get("subscription_tier", "free")`
- Same for any other `getattr` on `current_user` dict
- **Files:** `rivaflow/rivaflow/core/middleware/tier_check.py`

### 1.3 Fix admin_grapple.py auth dependency signatures
- All endpoints using `@require_admin` must declare `current_user: dict = Depends(get_current_user)` in function signature
- **Files:** `rivaflow/rivaflow/api/routes/admin_grapple.py`

### 1.4 Fix admin user detail leaking hashed_password
- Strip `hashed_password` from user dict before returning in response (~line 610)
- **Files:** `rivaflow/rivaflow/api/routes/admin.py`

### 1.5 Fix asyncio.run() in BackgroundTasks
- `_trigger_post_session_insight` (line 42) — replace `asyncio.run()` with direct await or `loop.run_in_executor`
- **Files:** `rivaflow/rivaflow/api/routes/sessions.py`

### 1.6 Fix boolean param in admin broadcast query
- Line ~1257: change `(1,)` → `(True,)` for `is_active` param
- **Files:** `rivaflow/rivaflow/api/routes/admin.py`

### 1.7 Fix dependency version mismatch
- Sync `cryptography` version across `requirements.txt`, root `pyproject.toml`, inner `pyproject.toml`
- Audit all three files for any other mismatches
- **Files:** `requirements.txt`, `pyproject.toml`, `rivaflow/pyproject.toml`

### 1.8 Remove stale CVE suppression
- Remove `CVE-2024-23342` suppression (python-jose is gone, now using PyJWT)
- **Files:** `.github/workflows/security.yml`

### 1.9 Fix Render deploy workflow honesty
- Either enable autoDeploy in render.yaml or add actual deploy trigger via Render API in deploy.yml
- **Files:** `render.yaml`, `.github/workflows/deploy.yml`

### 1.10 Add APScheduler distributed lock
- Use PG advisory lock (like migrate.py does) to prevent duplicate job execution across workers
- **Files:** `rivaflow/rivaflow/core/scheduler.py`

**Wave 1 Checkpoint:** Run `pytest tests/ -x -q` + `black rivaflow/ tests/` + `ruff check rivaflow/ tests/ --ignore=C901,N802,N818,UP042,F823`

---

## WAVE 2: Security Hardening

### 2.1 Implement refresh token rotation
- On each refresh, generate new refresh token, store it, delete old one, set new cookie
- **Files:** `rivaflow/rivaflow/core/services/auth_service.py`, `rivaflow/rivaflow/api/routes/auth.py`

### 2.2 Fix error message information leakage
- `goals.py` line 62: generic message instead of `str(e)`
- `integrations.py` line 134: generic message instead of `str(e)`
- Scan all routes for `detail=str(e)` or `detail=f"...{e}"` patterns and replace with generic messages
- **Files:** `rivaflow/rivaflow/api/routes/goals.py`, `rivaflow/rivaflow/api/routes/integrations.py`, others

### 2.3 Add request body size limit
- Configure in gunicorn/uvicorn or add middleware
- **Files:** `start.sh` or `rivaflow/rivaflow/api/main.py`

### 2.4 Strip hashed_password from UserRepository by default
- Make `_row_to_dict` exclude `hashed_password` unless explicitly requested
- Add a separate `get_by_id_with_password()` for auth use only
- **Files:** `rivaflow/rivaflow/db/repositories/user_repo.py`

**Wave 2 Checkpoint:** Run tests, lint, verify auth flow still works

---

## WAVE 3: Backend Code Quality

### 3.1 Extract error handling decorator for routes
- Create a decorator that handles the try/except + traceback + HTTPException pattern
- Apply to analytics.py (23 identical blocks) and other routes
- **Files:** New decorator in `rivaflow/rivaflow/api/` or `rivaflow/rivaflow/core/`, then `analytics.py` and others

### 3.2 Add response_model to top endpoints
- Prioritize: sessions, auth, profile, readiness, analytics, goals, admin
- Create Pydantic response models where missing
- **Files:** Route files + new response models in `rivaflow/rivaflow/core/models.py`

### 3.3 Replace SELECT * with explicit columns in critical repos
- Priority: `user_repo.py` (password leak risk), `session_repo.py`, `profile_repo.py`
- **Files:** `rivaflow/rivaflow/db/repositories/user_repo.py`, `session_repo.py`, `profile_repo.py`

### 3.4 Fix module-level SECRET_KEY evaluation
- Defer settings access in `auth.py` — use function-level access instead of module-level constant
- **Files:** `rivaflow/rivaflow/core/auth.py`

### 3.5 Fix module-level service instantiation in routes
- Move `service = SessionService()` etc. into endpoint functions or use FastAPI Depends()
- **Files:** `sessions.py`, `analytics.py`, `goals.py`, `profile.py`, and others

### 3.6 Deduplicate Limiter instances
- Create single shared limiter instance, import across routes
- **Files:** Create `rivaflow/rivaflow/api/rate_limit.py`, update all route files

### 3.7 Fix deprecated config.py imports
- Replace all `from rivaflow.config import get_db_type` with `from rivaflow.core.settings import settings`
- **Files:** `database.py`, `session_repo.py`, multiple services

**Wave 3 Checkpoint:** Full test suite, lint, ruff

---

## WAVE 4: Testing Coverage

### 4.1 Session scoring service tests
- Test each rubric (BJJ, competition, supplementary)
- Test graceful degradation with missing data
- Test score tier boundaries (29/30, 49/50, 69/70, 84/85)
- Test hook integration (session create/update triggers scoring)
- Test API endpoints (GET score, POST recalculate, POST backfill)
- **Files:** New `tests/test_session_scoring.py`

### 4.2 SmartPlanBanner unit tests
- Test `computeSmartStatus()` for all 7 priority levels
- Test `parseTimeToday()` helper
- **Files:** New `rivaflow/web/src/components/dashboard/__tests__/SmartPlanBanner.test.tsx`

### 4.3 Goals service tests
- Weekly/monthly goal progress calculation
- Edge cases (no sessions, goals set mid-week)
- All 6 API endpoints
- **Files:** New `tests/test_goals_routes.py`, `tests/test_goals_service.py`

### 4.4 Admin route tests
- User deactivation, bulk email, data management
- Auth enforcement (non-admin gets 403)
- **Files:** New `tests/test_admin_routes.py`

### 4.5 Gym timetable tests
- GymClassRepository CRUD
- GymService.get_timetable(), get_todays_classes()
- API endpoints
- **Files:** New `tests/test_gym_routes.py`

**Wave 4 Checkpoint:** Full test suite (should have significantly more coverage now)

---

## WAVE 5: Frontend Architecture

### 5.1 Split client.ts into domain-specific API modules
- Create `api/sessions.ts`, `api/analytics.ts`, `api/profile.ts`, etc.
- Keep `api/client.ts` as the base axios instance + interceptors only
- Update all imports across pages/components
- **Files:** `rivaflow/web/src/api/client.ts` → split into ~10 domain files

### 5.2 Break LogSession.tsx into sub-components
- Extract: ReadinessStep, SessionForm, TechniqueTracker, RollTracker, FightDynamicsSection, WhoopSyncSection
- Keep LogSession as orchestrator with shared state
- **Files:** `rivaflow/web/src/pages/LogSession.tsx` → new components in `components/sessions/`

### 5.3 Break DailyActionHero.tsx into separate files
- Extract: SmartPlanBanner, MorningPrompt, MiddayPrompt, EveningPrompt, CheckinBadges
- **Files:** `rivaflow/web/src/components/dashboard/DailyActionHero.tsx` → separate files

### 5.4 Break other god components
- Profile.tsx → extract ProfileForm, GoalsSection, GradingsSection, WhoopSection
- Grapple.tsx → extract SessionExtractionPanel, InsightsPanel, TechniqueQAPanel
- Reports.tsx → extract into tab-specific components
- EditSession.tsx → mirror LogSession decomposition
- **Files:** Multiple page files → extracted components

### 5.5 Fix duplicate interface definitions
- Remove duplicate `User` from AuthContext (use types/index.ts)
- Remove duplicate `WeekStats` from WeekAtGlance/ThisWeek
- Remove duplicate `Message` from Grapple/Chat
- Move `GymClass` from client.ts to types/index.ts
- Consolidate `ACTIVITY_COLORS`/`ACTIVITY_LABELS` into a single constants file
- **Files:** Various component files, `types/index.ts`

### 5.6 Fix dead code and deprecated APIs
- Remove `editGoal`/`setEditGoal` dead state in MonthlyGoals.tsx
- Replace native `confirm()`/`prompt()` with ConfirmDialog in MonthlyGoals.tsx
- Replace `onKeyPress` with `onKeyDown` in Chat.tsx
- Move `useInsightRefresh` to `utils/` (it's not a hook)
- **Files:** `MonthlyGoals.tsx`, `Chat.tsx`, `hooks/useInsightRefresh.ts`

### 5.7 Fix notification polling
- Add `document.visibilityState` check to Layout.tsx notification interval
- **Files:** `rivaflow/web/src/components/Layout.tsx`

### 5.8 Fix auth API base path inconsistency
- Align `auth.ts` base path with `client.ts` (`/api/v1` vs `/api`)
- **Files:** `rivaflow/web/src/api/auth.ts`

**Wave 5 Checkpoint:** `cd rivaflow/web && npm run build && npx tsc --noEmit` + run frontend tests

---

## WAVE 6: UX Quick Wins

### 6.1 Fix light mode elevation
- Set `--surfaceElev: #F0F1F4` in light mode (currently same as `--surface: #FFFFFF`)
- **Files:** `rivaflow/web/src/index.css` (and `web/src/index.css`)

### 6.2 Fix theme color meta tag
- Change from `#6C63FF` to match actual accent `#FF4D2D`
- **Files:** `rivaflow/web/index.html` (and `web/index.html`)

### 6.3 Default Reports date range to 30 days
- Change initial date range from 7 days to 30 days
- **Files:** `rivaflow/web/src/pages/Reports.tsx` (and `web/src/pages/Reports.tsx`)

### 6.4 Add session save celebration
- Replace static green checkmark with brief animation/confetti on session logged
- **Files:** `rivaflow/web/src/pages/LogSession.tsx` (and `web/`)

### 6.5 Unify brand colors
- Align Tailwind config combat-500, CSS var --accent, and meta tag to same value
- **Files:** `tailwind.config.js`/`tailwind.config.ts`, `index.css`, `index.html`

### 6.6 Reduce dashboard widget count
- Make GettingStarted, TodayClassesWidget, LatestInsightWidget, MyGameWidget conditional (only show when relevant data exists)
- Remove or collapse EngagementBanner
- **Files:** `rivaflow/web/src/pages/Dashboard.tsx` (and `web/`)

**Wave 6 Checkpoint:** Build frontend, verify visually reasonable via code review

---

## WAVE 7: DevOps & Infrastructure

### 7.1 Increase Sentry traces_sample_rate
- Change from 0.1 to 0.5 for better APM data during beta
- **Files:** `rivaflow/rivaflow/api/main.py`

### 7.2 Expand post-deploy smoke tests
- Add checks for auth endpoint, sessions endpoint, and frontend accessibility
- **Files:** `.github/workflows/deploy.yml`

### 7.3 Make gunicorn workers configurable
- Use `WEB_CONCURRENCY` env var instead of hardcoded `-w 2`
- **Files:** `start.sh`

### 7.4 Add scheduler health check
- Extend `/health` endpoint to report scheduler status
- **Files:** `rivaflow/rivaflow/api/main.py`

### 7.5 Add web/ sync pre-commit or automation note
- Document or automate the rsync between `rivaflow/web/` and `web/`
- **Files:** Add sync script or document in README

### 7.6 Clean up confusing deployment files
- Remove or move `rivaflow/deployment/docker-compose-traefik.yml` (it's for n8n, not RivaFlow)
- **Files:** `rivaflow/deployment/`

### 7.7 Add static asset cache headers
- Add `Cache-Control` for `/assets/*` in render.yaml static site config
- **Files:** `render.yaml`

**Wave 7 Checkpoint:** CI pipeline should pass with all changes

---

## WAVE 8: Frontend Performance & Polish

### 8.1 Remove unused react-window dependency OR implement virtualization
- Decision: use react-window for Sessions list, Glossary grid, Feed — OR remove from package.json
- **Files:** `rivaflow/web/package.json`, relevant list components

### 8.2 Fix SessionDetail fetching all sessions
- Replace `sessionsApi.list(1000)` with API endpoint that returns prev/next IDs
- Or compute prev/next from the sessions list page state
- **Files:** `rivaflow/web/src/pages/SessionDetail.tsx`, possibly backend route

### 8.3 Add useMemo for expensive computations
- Sessions.tsx: memoize filterAndSortSessions result
- Glossary.tsx: memoize getCategoryStats()
- Feed.tsx: memoize filteredItems
- **Files:** `Sessions.tsx`, `Glossary.tsx`, `Feed.tsx`

### 8.4 Fix package.json dependency placement
- Move `@types/react-window` and `serve` to devDependencies
- **Files:** `rivaflow/web/package.json`

### 8.5 Add sub-route error boundaries
- Wrap analytics charts, dashboard widgets in individual ErrorBoundary
- **Files:** `Reports.tsx`, `Dashboard.tsx`, relevant component areas

### 8.6 Add Vite chunk splitting
- Configure manual chunks for vendor, recharts, lucide-react
- **Files:** `rivaflow/web/vite.config.ts`

### 8.7 Gate console.log/error behind environment check
- Add a logger utility that only logs in development
- Replace direct console calls across ~45 files
- **Files:** New `utils/logger.ts`, update ~45 files

**Wave 8 Checkpoint:** Frontend build, check bundle size, run tests

---

## Final Sync & Verification

### After all waves:
1. Run full backend test suite: `cd /Users/rubertwolff/scratch && pytest tests/ rivaflow/tests/ -x -q`
2. Run lint: `black rivaflow/ tests/` then `ruff check rivaflow/ tests/ --ignore=C901,N802,N818,UP042,F823`
3. Run frontend build: `cd rivaflow/web && npm run build && npx vitest run`
4. Sync web/: `rsync -av --delete rivaflow/web/src/ web/src/ && rsync -av rivaflow/web/index.html web/index.html && rsync -av rivaflow/web/package.json web/package.json`
5. Verify diff sync: `diff -r rivaflow/web/src web/src`
6. Run `tsc --noEmit` to check for type errors
7. Commit with comprehensive message

---

## HARD REQUIREMENT
**All tests (root + inner) must have 100% pass rate by end of all waves. No skips, no warnings-as-pass. Fix all 44 failures and 17 errors in rivaflow/tests/.**

## Status Tracker

| Wave | Status | Notes |
|------|--------|-------|
| 1: Critical Safety | DONE | All 10 items complete, 408 root tests pass, lint clean |
| 2: Security Hardening | DONE | Token rotation, error leakage fixed, 2MB body limit, password stripped from repo |
| 3: Backend Code Quality | DONE | All items complete. 3.2 response_model, 3.3 explicit columns, 3.5 Depends pattern (commit 17bfe43) |
| 4: Testing Coverage | DONE | All 5 items complete (commit 4177b18): session scoring, goals, admin, gym timetable, SmartPlanBanner. 497 tests pass. |
| 5: Frontend Architecture | DONE | All items complete (commit 2e91f71): split client.ts, broke 6 god components into focused sub-components. |
| 6: UX Quick Wins | DONE | All items complete. 6.4 celebration animation (commit 17bfe43). 6.6 widgets already self-conditional. |
| 7: DevOps & Infrastructure | DONE | All items complete. 7.5 sync script, 7.6 removed stale deployment dir (commit 17bfe43) |
| 8: Frontend Performance | DONE | All items complete. 8.1 react-window removed, 8.2 SessionDetail fixed, 8.3 useMemo, 8.5 ErrorBoundary, 8.7 logger (commit 17bfe43) |
| Final Sync | DONE | 497 backend tests, 85 frontend tests, tsc clean, black clean, ruff clean, production build passes |
