# RivaFlow Testing Coverage & Gap Analysis

**Date:** 2026-02-11
**Repo root:** `/Users/rubertwolff/scratch/`
**CI test path:** `tests/` (collected by CI)
**Frontend test path:** `rivaflow/web/src/pages/__tests__/`

---

## Executive Summary

The RivaFlow codebase has **24 backend test files** with good depth in a few areas (auth, game plans, WHOOP, Grapple AI, analytics) but **major gaps** in many route modules, repositories, and services. Frontend coverage is minimal: **5 page tests** out of **47 pages**, with **zero component tests** for ~70 shared components. Integration tests cover basic user journeys but skip critical multi-user and payment flows.

**Overall coverage estimate:**
- Backend routes: ~30% of route modules have ANY test coverage
- Backend services: ~40% of service modules have ANY test coverage
- Backend repositories: ~15% of repository modules have direct test coverage
- Frontend pages: ~11% have tests
- Frontend components: 0% have dedicated tests

---

## 1. Backend Test Coverage

### 1.1 Test Files in `tests/` (CI-collected)

| Test File | What It Tests | Test Count (approx) | Quality |
|-----------|---------------|---------------------|---------|
| `test_auth_service.py` | Registration, login, refresh tokens, logout, password hashing, JWT, email validation | ~25 | **Excellent** - covers happy paths, error cases, edge cases |
| `test_session_service.py` | Session CRUD, techniques linking, autocomplete, class type detection, consecutive counts | ~7 | **Good** - covers core flows, missing update/delete |
| `test_report_service.py` | Report generation, date ranges, CSV export, rate calculations | ~6 | **Good** - covers key calculations |
| `test_reports_api.py` | Analytics API endpoints: performance overview, partner stats, technique breakdown, consistency, milestones | ~15 | **Good** - tests empty data, edge cases, date ranges, division-by-zero |
| `test_insights_analytics.py` | Math helpers (_pearson_r, _ewma, _shannon_entropy, _linear_slope), InsightsAnalyticsService edge cases | ~20 | **Excellent** - thorough edge case coverage |
| `test_game_plan_repo.py` | GamePlanRepository, GamePlanNodeRepository, GamePlanEdgeRepository CRUD | ~25 | **Excellent** - comprehensive CRUD + edge cases |
| `test_game_plan_routes.py` | /api/v1/game-plans/* endpoints (generate, get, update, delete, nodes, edges, focus) | ~20 | **Excellent** - covers 404s, auth, validation |
| `test_game_plan_service.py` | game_plan_service functions, _build_tree, template generation | ~15 | **Excellent** - covers tree building, service functions |
| `test_grapple_context_whoop.py` | WHOOP context in Grapple AI, partial data handling | ~4 | **Good** - tests data/no-data/partial scenarios |
| `test_grapple_llm_client.py` | Provider detection, cost calculation, chat fallback, provider status | ~12 | **Excellent** - tests all provider paths |
| `test_grapple_routes.py` | Grapple extract-session, save, insights, technique-qa, teaser, info, tier access | ~12 | **Good** - covers success + error paths |
| `test_social_routes.py` | Follow/unfollow, likes, comments, friend requests, feed | ~15 | **Good** - covers social lifecycle |
| `test_suggestion_engine.py` | Suggestion rules (high stress, soreness, consecutive gi, stale technique, green light, no readiness) | ~6 | **Good** - covers main rule branches |
| `test_whoop_analytics_engine.py` | Recovery-performance correlation, strain efficiency, HRV predictor, sleep analysis, cardiovascular drift | ~10 | **Good** - covers with/without data |
| `test_whoop_auto_sessions.py` | Auto-create from workouts, skip linked, toggle, profile defaults, backfill, no duplicates | ~10 | **Excellent** - thorough WHOOP auto-session coverage |
| `test_whoop_recovery.py` | Recovery cache CRUD, readiness auto-fill (high/medium/low), scope compatibility | ~12 | **Excellent** - covers recovery mapping ranges |
| `test_whoop_rules.py` | WHOOP-specific suggestion rules (low recovery, HRV drop, green recovery, HRV sustained decline) | ~12 | **Good** - tests fire/skip/no-data for each rule |
| `test_whoop_webhook.py` | Webhook signature verification, workout/recovery events, unknown events, no-secret bypass | ~7 | **Excellent** - security-critical, well-tested |
| `test_overtraining_whoop.py` | 6-factor overtraining risk with WHOOP biometrics | ~5 | **Good** - verifies factor structure and scoring |
| `cli/test_log_command.py` | CLI commands: log, rest, readiness, report, streak, progress, dashboard, auth, stats, export | ~15 | **Fair** - many tests use loose assertions, some xfail |
| `integration/test_user_journey.py` | Registration-to-session, daily workflow, weekly/monthly analytics, streaks, data export | ~8 | **Fair** - covers basics but some tests commented out |

### 1.2 Route Coverage Map

| Route Module | Prefix | Endpoint Count | Test Coverage | Notes |
|-------------|--------|---------------|---------------|-------|
| `auth.py` | `/api/v1/auth` | 8 | **Partial** | Service tested in `test_auth_service.py`; NO route-level tests for register/login/refresh/logout/me/forgot-password/reset-password |
| `sessions.py` | `/api/v1/sessions` | 10 | **Partial** | Service tested; NO route-level tests for create/update/delete/get/list/range/autocomplete/insights/with-rolls/partner-stats |
| `readiness.py` | `/api/v1/readiness` | 5 | **None** | Zero route tests; service only tested indirectly via integration |
| `analytics.py` | `/api/v1/analytics` | 25+ | **Partial** | `test_reports_api.py` covers performance-overview, partners, techniques, consistency, milestones; MISSING: readiness/trends, whoop/analytics, instructors, duration, time-of-day, gyms, class-types, weight, training-calendar, belt-distribution, all insights/* endpoints, fight-dynamics/*, whoop/* analytics (5 endpoints) |
| `profile.py` | `/api/v1/profile` | 5 | **None** | Zero tests for get/update/photo upload/delete/onboarding-status |
| `checkins.py` | `/api/v1/checkins` | 5 | **None** | Zero tests for today/week/tomorrow/midday/evening |
| `dashboard.py` | `/api/v1/dashboard` | 3 | **None** | Zero tests for summary/quick-stats/week-summary |
| `social.py` | `/api/v1/social` | 20+ | **Covered** | `test_social_routes.py` covers follow, likes, comments, friend requests, feed; MISSING: user search, recommended users, friend-suggestions, accept/decline requests |
| `grapple.py` | `/api/v1/grapple` | 12 | **Covered** | `test_grapple_routes.py` covers extract, save, insights, technique-qa, teaser, info; MISSING: chat, sessions CRUD, usage, insight chat |
| `game_plans.py` | `/api/v1/game-plans` | 10 | **Covered** | `test_game_plan_routes.py` comprehensive |
| `reports.py` | `/api/v1/reports` | 4 | **Partial** | `test_reports_api.py` covers analytics but NOT report-specific endpoints (week, month, range, csv) |
| `friends.py` | `/api/v1/friends` | 7 | **None** | Zero tests for list/instructors/partners/get/create/update/delete |
| `goals.py` | `/api/v1/goals` | 6 | **None** | Zero tests for current-week/summary/streaks/trend/targets |
| `glossary.py` | `/api/v1/glossary` | 7 | **None** | Zero tests; glossary only tested indirectly via session creation |
| `techniques.py` | `/api/v1/techniques` | 5 | **None** | Zero route tests |
| `videos.py` | `/api/v1/videos` | 4 | **None** | Zero tests |
| `events.py` | `/api/v1/events` | 9 | **None** | Zero tests (events + weight logs) |
| `integrations.py` | `/api/v1/integrations` | 17 | **None** | Zero route tests; WHOOP tested at service layer only |
| `groups.py` | `/api/v1/groups` | 8 | **None** | Zero tests |
| `notifications.py` | `/api/v1/notifications` | 7 | **None** | Zero tests |
| `photos.py` | `/api/v1/photos` | 5 | **None** | Zero tests |
| `chat.py` | `/api/v1/chat` | 1 | **None** | Zero tests (legacy Grapple chat) |
| `feedback.py` | `/api/v1/feedback` | 3 | **None** | Zero tests |
| `admin.py` | `/api/v1/admin` | 20+ | **None** | Zero tests for any admin endpoint |
| `admin_grapple.py` | `/api/v1/admin/grapple` | 6 | **None** | Zero tests |
| `suggestions.py` | `/api/v1/suggestions` | 1 | **None** | Service tested but route not tested |
| `rest.py` | `/api/v1/rest` | 1 | **None** | Zero tests |
| `streaks.py` | `/api/v1/streaks` | 2 | **None** | Zero tests |
| `gradings.py` | `/api/v1/gradings` | 6 | **None** | Zero tests |
| `milestones.py` | `/api/v1/milestones` | 4 | **None** | Partially tested via analytics tests |
| `webhooks.py` | `/api/v1/webhooks` | 1 | **Covered** | `test_whoop_webhook.py` comprehensive |
| `health.py` | `/health` | 3 | **None** | Zero tests |
| `users.py` | `/api/v1/users` | 4 | **None** | Zero tests |
| `waitlist.py` | `/api/v1/waitlist` | 2 | **None** | Zero tests |
| `llm_tools.py` | `/api/v1/llm-tools` | 2 | **None** | Zero tests |
| `coach_preferences.py` | `/api/v1/coach-preferences` | 2 | **None** | Zero tests |
| `training_goals.py` | `/api/v1/training-goals` | 5 | **None** | Zero tests |
| `transcribe.py` | `/api/v1/transcribe` | 1 | **None** | Zero tests |
| `gyms.py` | `/api/v1/gyms` | 2 | **None** | Zero tests |
| `feed.py` | `/api/v1/feed` | 2 | **Partial** | Tested via `test_social_routes.py` |

### 1.3 Repository Coverage Map

| Repository | Test Coverage | Notes |
|-----------|--------------|-------|
| `session_repo.py` | **Partial** | Tested via session service + WHOOP auto-sessions; no direct CRUD tests |
| `readiness_repo.py` | **Partial** | Tested via conftest factories; no direct unit tests |
| `user_repo.py` | **Partial** | Tested via auth service tests; no direct CRUD tests |
| `profile_repo.py` | **Partial** | Tested via auth registration (creates profile); no direct tests |
| `refresh_token_repo.py` | **Partial** | Tested via auth service; no direct tests |
| `game_plan_repo.py` | **Covered** | `test_game_plan_repo.py` comprehensive |
| `game_plan_node_repo.py` | **Covered** | `test_game_plan_repo.py` comprehensive |
| `game_plan_edge_repo.py` | **Covered** | `test_game_plan_repo.py` comprehensive |
| `whoop_recovery_cache_repo.py` | **Covered** | `test_whoop_recovery.py` comprehensive |
| `whoop_workout_cache_repo.py` | **Partial** | Tested via WHOOP auto-sessions |
| `whoop_connection_repo.py` | **Partial** | Tested via WHOOP auto-sessions |
| `glossary_repo.py` | **Partial** | Tested indirectly via session service |
| `session_technique_repo.py` | **Partial** | Tested indirectly via session service |
| `friend_repo.py` | **Partial** | Tested via conftest fixture; no direct tests |
| `social_connection_repo.py` | **Partial** | Tested via social route tests |
| `activity_like_repo.py` | **Partial** | Tested via social route tests |
| `activity_comment_repo.py` | **Partial** | Tested via social route tests |
| `streak_repo.py` | **Partial** | Tested via auth registration (creates streaks) |
| `technique_repo.py` | **None** | Zero tests |
| `video_repo.py` | **None** | Zero tests |
| `notification_repo.py` | **None** | Zero tests |
| `milestone_repo.py` | **None** | Zero tests |
| `grading_repo.py` | **None** | Zero tests |
| `gym_repo.py` | **None** | Zero tests |
| `feedback_repo.py` | **None** | Zero tests |
| `checkin_repo.py` | **None** | Zero tests |
| `goal_progress_repo.py` | **None** | Zero tests |
| `chat_message_repo.py` | **None** | Zero tests |
| `chat_session_repo.py` | **None** | Zero tests |
| `password_reset_token_repo.py` | **None** | Zero tests |
| `relationship_repo.py` | **None** | Zero tests |
| `session_roll_repo.py` | **None** | Zero tests |
| `friend_suggestions_repo.py` | **None** | Zero tests |
| `activity_photo_repo.py` | **None** | Zero tests |
| `ai_insight_repo.py` | **None** | Zero tests |
| `coach_preferences_repo.py` | **None** | Zero tests |
| `email_drip_repo.py` | **None** | Zero tests |
| `events_repo.py` | **None** | Zero tests |
| `groups_repo.py` | **None** | Zero tests |
| `training_goal_repo.py` | **None** | Zero tests |
| `waitlist_repo.py` | **None** | Zero tests |
| `weight_log_repo.py` | **None** | Zero tests |
| `whoop_oauth_state_repo.py` | **None** | Zero tests |
| `session_event_repo.py` | **None** | Zero tests |

### 1.4 Service Coverage Map

| Service | Test Coverage | Notes |
|---------|--------------|-------|
| `auth_service.py` | **Covered** | `test_auth_service.py` comprehensive |
| `session_service.py` | **Covered** | `test_session_service.py` good coverage |
| `report_service.py` | **Covered** | `test_report_service.py` good coverage |
| `analytics_service.py` | **Partial** | Tested via `test_reports_api.py` (performance overview); many analytics methods untested |
| `insights_analytics.py` | **Covered** | `test_insights_analytics.py` + `test_overtraining_whoop.py` |
| `suggestion_engine.py` | **Covered** | `test_suggestion_engine.py` |
| `game_plan_service.py` | **Covered** | `test_game_plan_service.py` |
| `game_plan_template_service.py` | **Covered** | `test_game_plan_service.py` |
| `whoop_service.py` | **Covered** | `test_whoop_auto_sessions.py` + `test_whoop_recovery.py` |
| `whoop_analytics_engine.py` | **Covered** | `test_whoop_analytics_engine.py` |
| `whoop_client.py` | **None** | Zero tests for API client |
| `grapple/llm_client.py` | **Covered** | `test_grapple_llm_client.py` |
| `grapple/context_builder.py` | **Partial** | WHOOP context tested; user/session context NOT tested |
| `grapple/ai_insight_service.py` | **Partial** | Tested indirectly via routes; no direct unit tests |
| `grapple/session_extraction_service.py` | **None** | Only tested via mocked route tests |
| `grapple/glossary_rag_service.py` | **None** | Only tested via mocked route tests |
| `grapple/rate_limiter.py` | **None** | Zero tests |
| `grapple/token_monitor.py` | **None** | Zero tests |
| `readiness_service.py` | **Partial** | Tested indirectly via suggestion engine; no direct tests |
| `streak_service.py` | **Partial** | Tested via integration tests; no direct unit tests |
| `streak_analytics.py` | **None** | Zero tests |
| `social_service.py` | **Partial** | Tested via route tests |
| `feed_service.py` | **Partial** | Tested via route tests |
| `friend_service.py` | **None** | Zero tests |
| `friend_suggestions_service.py` | **None** | Zero tests |
| `email_service.py` | **None** | Zero tests |
| `notification_service.py` | **None** | Zero tests |
| `profile_service.py` | **None** | Zero tests |
| `user_service.py` | **None** | Zero tests |
| `privacy_service.py` | **None** | Zero tests |
| `tier_access_service.py` | **Partial** | Tested via grapple route (free user denied); no direct tests |
| `video_service.py` | **None** | Zero tests |
| `technique_service.py` | **None** | Zero tests |
| `technique_analytics.py` | **None** | Zero tests |
| `performance_analytics.py` | **None** | Zero tests |
| `readiness_analytics.py` | **None** | Zero tests |
| `gym_service.py` | **None** | Zero tests |
| `grading_service.py` | **None** | Zero tests |
| `goals_service.py` | **None** | Zero tests |
| `glossary_service.py` | **None** | Zero tests |
| `milestone_service.py` | **None** | Zero tests |
| `rest_service.py` | **None** | Zero tests |
| `insight_service.py` | **None** | Zero tests |
| `session_insight_service.py` | **None** | Zero tests |
| `audit_service.py` | **None** | Zero tests |
| `storage_service.py` | **None** | Zero tests |
| `fight_dynamics_service.py` | **None** | Zero tests |
| `training_goals_service.py` | **None** | Zero tests |

---

## 2. Frontend Test Coverage

### 2.1 Page Test Coverage Map

| Page Component | Test File | Coverage | Notes |
|---------------|-----------|---------|-------|
| `Dashboard.tsx` | `Dashboard.test.tsx` | **Covered** | Renders title, quick actions; child components mocked |
| `Login.tsx` | `Login.test.tsx` | **Covered** | Form inputs, submit, error handling, loading state, navigation |
| `Register.tsx` | `Register.test.tsx` | **Covered** | Form fields, validation (short password, mismatch), submit, error display |
| `Sessions.tsx` | `Sessions.test.tsx` | **Covered** | Loading skeletons, session list, empty state, search controls |
| `Techniques.tsx` | `Techniques.test.tsx` | **Covered** | Loading skeletons, empty state, technique table, stale alert |
| `AdminContent.tsx` | --- | **None** | No tests |
| `AdminDashboard.tsx` | --- | **None** | No tests |
| `AdminFeedback.tsx` | --- | **None** | No tests |
| `AdminGrapple.tsx` | --- | **None** | No tests |
| `AdminGyms.tsx` | --- | **None** | No tests |
| `AdminTechniques.tsx` | --- | **None** | No tests |
| `AdminUsers.tsx` | --- | **None** | No tests |
| `AdminWaitlist.tsx` | --- | **None** | No tests |
| `Chat.tsx` | --- | **None** | No tests |
| `CoachSettings.tsx` | --- | **None** | No tests |
| `ContactUs.tsx` | --- | **None** | No tests |
| `EditReadiness.tsx` | --- | **None** | No tests |
| `EditRest.tsx` | --- | **None** | No tests |
| `EditSession.tsx` | --- | **None** | No tests |
| `Events.tsx` | --- | **None** | No tests |
| `FAQ.tsx` | --- | **None** | No tests |
| `Feed.tsx` | --- | **None** | No tests |
| `FightDynamics.tsx` | --- | **None** | No tests |
| `FindFriends.tsx` | --- | **None** | No tests |
| `ForgotPassword.tsx` | --- | **None** | No tests |
| `Friends.tsx` | --- | **None** | No tests |
| `Glossary.tsx` | --- | **None** | No tests |
| `Grapple.tsx` | --- | **None** | No tests |
| `Groups.tsx` | --- | **None** | No tests |
| `LogSession.tsx` | --- | **None** | No tests -- **CRITICAL: primary data entry page** |
| `MonthlyGoals.tsx` | --- | **None** | No tests |
| `MovementDetail.tsx` | --- | **None** | No tests |
| `MyGame.tsx` | --- | **None** | No tests |
| `Privacy.tsx` | --- | **None** | No tests |
| `Profile.tsx` | --- | **None** | No tests |
| `Readiness.tsx` | --- | **None** | No tests -- **CRITICAL: daily check-in page** |
| `ReadinessDetail.tsx` | --- | **None** | No tests |
| `Reports.tsx` | --- | **None** | No tests |
| `ResetPassword.tsx` | --- | **None** | No tests |
| `RestDetail.tsx` | --- | **None** | No tests |
| `SessionDetail.tsx` | --- | **None** | No tests |
| `Terms.tsx` | --- | **None** | No tests |
| `UserProfile.tsx` | --- | **None** | No tests |
| `Videos.tsx` | --- | **None** | No tests |
| `Waitlist.tsx` | --- | **None** | No tests |

**Frontend pages with tests: 5 out of 47 (10.6%)**

### 2.2 Component Test Coverage

**There are ZERO dedicated component tests.** The `rivaflow/web/src/test/setup.ts` file only configures the test environment. None of the ~70 shared components have tests:

**Critical untested components:**
- `PrivateRoute.tsx` -- auth guard, foundational to app security
- `Layout.tsx` -- app shell
- `ErrorBoundary.tsx` -- error handling
- `Toast.tsx` -- user feedback
- `ConfirmDialog.tsx` -- destructive action confirmation
- `QuickLog.tsx` -- quick session logging
- `ReadinessResult.tsx` -- readiness score display
- `SessionInsights.tsx` -- AI insight display
- `BottomNav.tsx` / `Sidebar.tsx` -- navigation
- All `dashboard/*` components (12 components)
- All `analytics/*` components (20 components)
- All `ui/*` components (15 components)
- `AuthContext.tsx` -- authentication state management
- `ToastContext.tsx` -- toast state management

### 2.3 Frontend Test Quality Assessment

The existing 5 page tests are **well-written behavioral tests**, not snapshots:

**Strengths:**
- Tests user interactions (form fills, clicks, navigation)
- Tests error states (login failure, registration errors)
- Tests loading states (skeletons, disabled buttons)
- Tests empty states
- Proper use of `waitFor` for async operations
- Mocking of API clients and context providers

**Weaknesses:**
- Dashboard test is shallow (only checks title and one button text)
- Dashboard mocks ALL child components, so no real rendering is tested
- No tests verify API calls are made with correct parameters (except Login)
- No accessibility testing

---

## 3. Test Quality Assessment

### 3.1 Tests That Actually Test the Right Things

**Strong examples:**
- `test_auth_service.py`: Tests both happy and error paths, verifies database state, checks security properties (password not in response, inactive user blocked)
- `test_game_plan_repo.py`: Tests CRUD + edge cases (wrong user, not found, no fields)
- `test_whoop_webhook.py`: Tests signature verification (security-critical), both valid and invalid signatures

### 3.2 Weak or Potentially Misleading Tests

**Tests with loose assertions:**
- `cli/test_log_command.py`: Many tests use `assert result.exit_code == 0 or "rest" in result.output.lower()` -- this means a failing test could still pass if the output contains common words
- `test_grapple_context_whoop.py` `test_insight_includes_whoop_recovery`: Has a `try/except Exception: pass` block that swallows all errors, then only checks mock calls -- the core function may have failed entirely
- `integration/test_user_journey.py` `test_invalid_data_rejection`: Marked as `@pytest.mark.skip` -- this means there is NO validation of negative duration values

### 3.3 Flaky Test Patterns

- **Date dependency**: Several tests use `date.today()` which could fail around midnight. For example, `test_reports_api.py` creates sessions on `date.today()` then queries a range. If the test crosses midnight, it will fail.
- **Order independence**: Tests properly use the `temp_db` fixture which creates a fresh database per test, so order dependency is not an issue.
- **Async test handling**: `test_grapple_context_whoop.py` uses `asyncio.get_event_loop().run_until_complete()` which is deprecated; should use `@pytest.mark.asyncio`.

### 3.4 Edge Cases Coverage

**Well-covered:**
- Division by zero in analytics (tested explicitly)
- Empty data / no data scenarios
- Null/None values in WHOOP data
- Invalid authentication tokens

**Missing edge cases:**
- Concurrent requests (no concurrency tests)
- Very large datasets (no performance/stress tests)
- Unicode/special characters in names, notes, gym names
- SQL injection vectors (no security-focused input tests)
- Date boundary conditions (sessions at midnight, timezone issues)
- Session/readiness data with all-zero values
- Maximum field lengths
- Rate limiting behavior (endpoints have rate limits but no tests verify them)

---

## 4. Integration Test Gaps

### 4.1 Current Integration Coverage (`tests/integration/`)

| Journey | Status | File |
|---------|--------|------|
| Registration to first session | **Covered** | `test_user_journey.py` |
| Daily workflow (readiness + session) | **Covered** | `test_user_journey.py` |
| Weekly analytics after sessions | **Covered** | `test_user_journey.py` |
| Monthly progress tracking | **Covered** | `test_user_journey.py` |
| Data export | **Covered** | `test_user_journey.py` |
| Streak buildup and break | **Covered** | `test_user_journey.py` |
| Duplicate session handling | **Covered** | `test_user_journey.py` |
| Multi-user follow workflow | **Commented out** | `test_user_journey.py` |
| Social feed with followers | **Commented out** | `test_user_journey.py` |

### 4.2 Missing Critical User Journeys

| Journey | Risk Level | Description |
|---------|------------|-------------|
| **WHOOP OAuth flow** | **CRITICAL** | Authorize -> callback -> token storage -> sync. No integration test. |
| **Password reset flow** | **HIGH** | Forgot password -> email -> reset token -> new password. No test. |
| **Profile setup + onboarding** | **HIGH** | New user completes profile -> onboarding status updates. No test. |
| **Grapple AI chat conversation** | **HIGH** | User sends message -> context built -> LLM response -> stored. No integration test. |
| **Session edit + re-analysis** | **MEDIUM** | User edits session -> techniques updated -> analytics recalculated. No test. |
| **Multi-daily checkins** | **MEDIUM** | Morning checkin -> midday checkin -> evening checkin. No test for the Wave 5 feature. |
| **Group creation + join** | **MEDIUM** | Create group -> invite members -> members join. No test. |
| **Event lifecycle** | **MEDIUM** | Create event -> prep checklist -> event day -> weight log. No test. |
| **Photo upload to session** | **LOW** | Upload photo -> link to session -> display in feed. No test. |
| **Notification delivery** | **MEDIUM** | Social action -> notification created -> user reads. No test. |
| **Admin user management** | **MEDIUM** | Admin lists users -> edits tier -> broadcasts email. No test. |
| **Drip email scheduling** | **LOW** | User registers -> drip emails scheduled -> sent at intervals. No test. |
| **Training goal lifecycle** | **MEDIUM** | Create goal -> track progress -> complete/fail. No test. |
| **Session deletion cascade** | **MEDIUM** | Delete session -> techniques unlinked -> analytics updated -> feed updated. No test. |

---

## 5. Priority Recommendations

### Tier 1: CRITICAL (write these first)

| Priority | What to Test | Why | Effort |
|----------|-------------|-----|--------|
| 1 | **Auth route tests** (`/api/v1/auth/*`) | Auth is the gateway to the entire app. Route-level tests verify middleware, rate limiting, response schemas. Service tests exist but route tests don't. | Medium |
| 2 | **Session route tests** (`/api/v1/sessions/*`) | Core feature -- session CRUD is the most-used functionality. No route tests exist. | Medium |
| 3 | **Readiness route tests** (`/api/v1/readiness/*`) | Daily check-in is a core user flow. Zero tests. | Low |
| 4 | **Profile route tests** (`/api/v1/profile/*`) | Profile is required for onboarding and many features. Zero tests. | Low |
| 5 | **LogSession.tsx frontend test** | Primary data entry page. Most important user interaction. | Medium |
| 6 | **Readiness.tsx frontend test** | Daily check-in page. Second most important user interaction. | Medium |
| 7 | **Integration route tests** (`/api/v1/integrations/whoop/*`) | WHOOP integration has 17 endpoints with zero route tests. OAuth callback is security-critical. | High |
| 8 | **Password reset integration test** | Forgot-password flow is untested end-to-end. Security-critical. | Medium |

### Tier 2: HIGH (write these second)

| Priority | What to Test | Why | Effort |
|----------|-------------|-----|--------|
| 9 | **Checkins route tests** (`/api/v1/checkins/*`) | Wave 5 multi-daily checkins feature has zero tests. | Low |
| 10 | **Notification route tests** | Notifications drive user engagement. Zero tests. | Low |
| 11 | **Goals route tests** | Weekly goals and training targets are untested. | Low |
| 12 | **Friends route tests** (`/api/v1/friends/*`) | Training partners/instructors CRUD is untested. | Low |
| 13 | **Gradings route tests** | Belt progression tracking is untested. | Low |
| 14 | **PrivateRoute.tsx component test** | Auth guard is foundational. Needs test for redirect behavior. | Low |
| 15 | **AuthContext.tsx test** | Authentication state management is untested. | Medium |
| 16 | **EditSession.tsx frontend test** | Session editing is a critical path. | Medium |
| 17 | **Grapple.tsx frontend test** | AI coach is a premium feature. | Medium |

### Tier 3: MEDIUM (write these as capacity allows)

| Priority | What to Test | Why | Effort |
|----------|-------------|-----|--------|
| 18 | **Admin route tests** | Admin has 20+ endpoints, all untested. | High |
| 19 | **Groups route tests** | Group feature has 8 endpoints, all untested. | Medium |
| 20 | **Events route tests** | Events + weight logs have 9 endpoints, all untested. | Medium |
| 21 | **Feed.tsx / Friends.tsx frontend tests** | Social features need UI tests. | Medium |
| 22 | **Dashboard widget component tests** | 12 dashboard components are all untested. | High |
| 23 | **Analytics chart component tests** | 20 chart components are untested. | High |
| 24 | **Rate limiter tests** | `grapple/rate_limiter.py` has zero tests. | Low |
| 25 | **Email service tests** | Email sending is completely untested. | Medium |
| 26 | **Storage service tests** | File upload/storage is untested. | Medium |

### Tier 4: LOW (nice to have)

| Priority | What to Test | Why | Effort |
|----------|-------------|-----|--------|
| 27 | Health endpoint tests | Simple but good for CI validation. | Trivial |
| 28 | Waitlist route tests | Low traffic feature. | Low |
| 29 | LLM tools route tests | Internal API. | Low |
| 30 | Static page tests (FAQ, Terms, Privacy, ContactUs) | Low risk. | Trivial |
| 31 | UI primitive component tests (Button, Card, Chip, etc.) | Stable, low change rate. | Low |

---

## 6. Specific Test Recommendations

### 6.1 Auth Route Tests (`tests/test_auth_routes.py`)

```
- test_register_endpoint_returns_tokens
- test_register_endpoint_duplicate_email_422
- test_register_endpoint_invalid_email_422
- test_register_endpoint_short_password_422
- test_register_endpoint_rate_limited
- test_login_endpoint_success
- test_login_endpoint_wrong_password_401
- test_login_endpoint_nonexistent_user_401
- test_login_endpoint_inactive_user_401
- test_refresh_endpoint_success
- test_refresh_endpoint_invalid_token_401
- test_logout_endpoint_success
- test_logout_endpoint_requires_auth
- test_logout_all_endpoint
- test_me_endpoint_returns_user_info
- test_me_endpoint_requires_auth
- test_forgot_password_sends_email (mock email)
- test_forgot_password_nonexistent_email_still_200
- test_reset_password_success
- test_reset_password_invalid_token
```

### 6.2 Session Route Tests (`tests/test_session_routes.py`)

```
- test_create_session_success_201
- test_create_session_with_techniques
- test_create_session_with_rolls
- test_create_session_requires_auth
- test_update_session_success
- test_update_session_not_found_404
- test_update_session_wrong_user_404
- test_delete_session_success
- test_delete_session_not_found_404
- test_get_session_success
- test_get_session_not_found_404
- test_list_sessions_paginated
- test_list_sessions_empty
- test_get_sessions_by_range
- test_autocomplete_data
- test_session_insights_endpoint
- test_session_with_rolls_endpoint
- test_partner_stats_endpoint
```

### 6.3 Frontend LogSession Test

```
- renders all form fields (date, class type, gym, duration, intensity)
- renders roll logging section
- renders technique selection
- submits form with correct data
- validates required fields
- shows error on API failure
- navigates to session detail on success
- pre-fills from WHOOP data when available
```

---

## 7. Summary Statistics

| Category | Total | Tested | Coverage |
|----------|-------|--------|----------|
| Route modules (non-__init__) | 37 | 7 fully + 4 partial | ~30% |
| Repository modules | 42 | 3 fully + 10 partial | ~31% indirect |
| Service modules | 44 | 10 fully + 6 partial | ~36% |
| Frontend pages | 47 | 5 | 10.6% |
| Frontend components | ~70 | 0 | 0% |
| Frontend contexts/hooks | 5 | 0 | 0% |
| Integration journeys | 14 critical | 5 covered + 2 commented out | ~36% |
| Backend test files | 24 | --- | --- |
| Frontend test files | 5 | --- | --- |

**Key takeaway:** The tests that exist are generally well-written and test real behavior. The problem is breadth -- large sections of the codebase have zero test coverage. The highest-risk gaps are in auth routes (no route-level tests despite service tests), session routes (no route-level tests), WHOOP integration routes (17 endpoints, zero route tests), and the frontend (only 5 of 47 pages tested, zero component tests).
