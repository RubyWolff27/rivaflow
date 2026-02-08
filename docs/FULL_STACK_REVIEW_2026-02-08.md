# RivaFlow Full-Stack Review — February 8, 2026

## Overall Health: Solid Beta, Needs Hardening

The app is feature-rich and well-architected for a beta. The core training loop works, AI features are impressive, and the codebase is clean. But there are gaps that need closing before scaling beyond beta users.

---

## Status Tracker

### Sprint 1 (Immediate) — COMPLETE
- [x] 1. Set up automated database backups — `scripts/backup_db.sh` created
- [x] 2. Fix CVEs — pip-audit clean (1 known, no upstream fix), `security.yml` rewritten
- [x] 3. Delete conflicting `rivaflow/render.yaml` — deleted
- [x] 4. Add CI check to enforce `web/` sync — `diff -r` step in `test.yml`
- [x] 5. Broaden SQL f-string validation — whitelists + ValueError in 7 files

### Sprint 2 (This Month)
- [ ] 6. Add route-level tests for auth, sessions, readiness, admin (target 40% coverage)
- [ ] 7. Make `ALLOWED_ORIGINS` required in production (fail-fast)
- [ ] 8. Add configurable connection pool via env vars
- [ ] 9. Escape user inputs in email templates
- [ ] 10. Post-signup onboarding flow

### Sprint 3 (Next Month)
- [ ] 11. Payment integration (Stripe)
- [ ] 12. Simplify session logging form (hide advanced by default)
- [ ] 13. Reorder dashboard (readiness first, week at glance, then insights)
- [ ] 14. Implement request tracing middleware
- [ ] 15. Structured JSON logging

### Ongoing
- [ ] Increase test coverage target: 40% → 60% → 80%
- [ ] Monthly dependency audit
- [ ] Quarterly security review

---

## CRITICAL (Fix Before Scaling)

| # | Finding | Domain | Impact | Status |
|---|---------|--------|--------|--------|
| 1 | **No database backups** — Free-tier Render PG has no auto-backups, expires after 90 days | DevOps | Total data loss risk | |
| 2 | **34 known CVEs in Python deps** — `urllib3`, `werkzeug`, `protobuf`, `python-multipart` | Security | Remote code execution risk | |
| 3 | **Conflicting render.yaml files** — root vs inner have different service configs | DevOps | Deployment confusion | |
| 4 | **No payment integration** — UpgradePrompt has empty TODO, no Stripe/payment flow | Product | Revenue blocked | |
| 5 | **Dynamic SQL via f-strings** — `session_repo.py:236`, `grading_repo.py:134`, others build UPDATE/ORDER BY with f-strings. Whitelisted fields mitigate but pattern is fragile | Security | SQL injection risk | |

---

## HIGH (Fix This Month)

| # | Finding | Domain | Status |
|---|---------|--------|--------|
| 6 | **Auth tokens in localStorage** — XSS can steal tokens. Should use HTTPOnly cookies | Security | |
| 7 | **Dual frontend directories** — `rivaflow/web/` and `web/` must be manually synced, no CI enforcement | DevOps | |
| 8 | **Test coverage ~10%** — 24 of 35 API route files have zero tests. Frontend has only 5 test files | Testing | |
| 9 | **No secrets rotation** — SECRET_KEY generated once, never rotated | DevOps | |
| 10 | **Email template injection** — User names injected into HTML emails without escaping | Security | |
| 11 | **Module-level service instantiation** — All route files create services at import time | Backend | |
| 12 | **Session logging form is 1,500+ lines** — Mobile friction, cognitive overload | Product | |
| 13 | **No post-signup onboarding** — New users land on dashboard with no guidance | Product | |
| 14 | **Connection pool hardcoded** — `minconn=2, maxconn=40` with no env var config | DevOps | |
| 15 | **Inconsistent dep versions** — Root vs inner pyproject.toml pin different versions | DevOps | |

---

## MEDIUM (Fix This Quarter)

| # | Finding | Domain | Status |
|---|---------|--------|--------|
| 16 | Weak password requirements (length only, no complexity) | Security | |
| 17 | No request tracing/correlation IDs | DevOps | |
| 18 | N+1 queries in analytics (glossary lookups in loops) | Backend | |
| 19 | Reports activity filter paywalled even for basic overview | Product | |
| 20 | Concurrent token refresh race condition | Frontend | |
| 21 | Sessions page loads 1,000 items into DOM | Frontend | |
| 22 | CSP allows `unsafe-inline` for styles | Security | |
| 23 | No structured JSON logging for production | DevOps | |
| 24 | 109 console.log calls ship to production | Frontend | |
| 25 | CORS falls back to localhost in production if ALLOWED_ORIGINS not set | Backend | |
| 26 | Grapple AI lacks user context for personalization | Product | |
| 27 | Dashboard info hierarchy buries key widgets | Product | |
| 28 | `admin.py` is 1,018 lines — should be split | Backend | |
| 29 | Readiness slider labels confusing | Product | |
| 30 | No graceful shutdown handling in start.sh | DevOps | |

---

## LOW (Nice-to-Have)

| # | Finding | Domain | Status |
|---|---------|--------|--------|
| 31 | Bcrypt silently truncates passwords >72 bytes | Security | |
| 32 | User emails logged in warning messages | Security | |
| 33 | No lazy loading for heavy chart components | Frontend | |
| 34 | Missing form validation abstraction | Frontend | |
| 35 | No API versioning deprecation strategy documented | DevOps | |
| 36 | Toast context has removeToast but doesn't export it | Frontend | |
| 37 | No database migration dry-run capability | DevOps | |
| 38 | Static files served from Python app (should be CDN) | DevOps | |

---

## What's Working Well

- Parameterized queries used consistently (`convert_query()`)
- OpenAPI docs disabled in production
- SQLite database file permissions set to 0o600
- Password reset prevents user enumeration
- Custom exception hierarchy with actionable messages
- Solid middleware stack (security headers, HSTS, compression, versioning)
- Rate limiting on auth endpoints
- Grapple AI well-tested (80% coverage)
- CSS variable design system with light/dark mode
- Accessibility patterns (skip-to-content, ARIA labels, focus traps)
- Dual DB support (SQLite dev, PostgreSQL prod)

---

## Review Agents

| Agent | Focus | Key Findings |
|-------|-------|-------------|
| Security | Auth, CORS, SQL injection, XSS, secrets, email | 2 critical, 5 high, 5 medium |
| Backend Quality | Architecture, API design, DB layer, performance | Module-level instantiation, N+1 queries, long methods |
| Frontend Quality | React patterns, TypeScript, a11y, performance | `any` types, race conditions, 109 console.logs |
| Testing Coverage | Backend + frontend test gaps | ~10% coverage, 24/35 route files untested |
| DevOps | Render, CI/CD, DB, monitoring, dependencies | No backups, CVEs, conflicting configs |
| Product/UX | User flows, onboarding, IA, tier system | No payment, no onboarding, form overload |
