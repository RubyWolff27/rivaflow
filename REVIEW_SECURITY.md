# RivaFlow Security Review

**Date:** 2026-02-11
**Scope:** Full codebase security audit (OWASP-oriented)
**Repo root:** `/Users/rubertwolff/scratch/`
**Reviewer:** Pre-production security audit

---

## Executive Summary

RivaFlow demonstrates a generally security-conscious architecture with many best practices already in place: bcrypt password hashing, parameterized SQL queries, JWT with refresh token rotation, Fernet-encrypted WHOOP OAuth tokens, admin role enforcement via dependency injection, CORS whitelisting, rate limiting, security headers, and CSP. However, several findings ranging from Medium to High severity require attention before production hardening is complete.

**Findings by Severity:**
- Critical: 0
- High: 4
- Medium: 8
- Low: 7

---

## 1. Authentication & Authorization

### 1.1 JWT Token Storage in localStorage (HIGH)

**Severity:** HIGH
**CVSS:** 7.1 (High) -- AV:N/AC:L/PR:N/UI:R/S:U/C:H/I:L/A:N
**Files:**
- `/Users/rubertwolff/scratch/web/src/contexts/AuthContext.tsx` lines 66-67, 94-95
- `/Users/rubertwolff/scratch/web/src/api/client.ts` line 28

**Description:** Access tokens and refresh tokens are stored in `localStorage`, which is accessible to any JavaScript running on the page. If an XSS vulnerability is found (even in a third-party dependency), an attacker can exfiltrate both tokens and gain full account access.

**Evidence:**
```typescript
// AuthContext.tsx:66-67
localStorage.setItem('access_token', response.data.access_token);
localStorage.setItem('refresh_token', response.data.refresh_token);
```

**Recommendation:** Migrate to `httpOnly`, `Secure`, `SameSite=Strict` cookies for the refresh token. The access token can remain in memory (not localStorage) and be refreshed via the cookie-based refresh flow. This eliminates token theft via XSS.

---

### 1.2 WHOOP OAuth Callback Lacks JWT Protection (MEDIUM)

**Severity:** MEDIUM
**CVSS:** 5.3 -- AV:N/AC:H/PR:N/S:U/C:L/I:L/A:N
**File:** `/Users/rubertwolff/scratch/rivaflow/rivaflow/api/routes/integrations.py` lines 66-97

**Description:** The WHOOP OAuth callback endpoint (`/api/v1/integrations/whoop/callback`) is not JWT-protected. Authentication relies solely on the `state` parameter (a CSRF token). The state token is single-use and time-limited (10 minutes), which is standard OAuth practice. However, the redirect URL at line 83 directly interpolates the `error` parameter from WHOOP into the redirect URL without sanitization.

**Evidence:**
```python
# integrations.py:83
return RedirectResponse(f"{frontend_url}/profile?whoop=error&reason={error}")
```

**Impact:** An attacker could craft a callback URL with a malicious `error` parameter value containing URL-encoded characters. Since `RedirectResponse` doesn't escape query parameters, this could lead to header injection or open redirect in some edge cases.

**Recommendation:** URL-encode the `error` parameter using `urllib.parse.quote()` before including it in the redirect URL.

---

### 1.3 WHOOP Zones Batch Endpoint -- Potential IDOR (MEDIUM)

**Severity:** MEDIUM
**CVSS:** 5.3 -- AV:N/AC:L/PR:L/S:U/C:L/I:N/A:N
**File:** `/Users/rubertwolff/scratch/rivaflow/rivaflow/api/routes/integrations.py` lines 439-479

**Description:** The `/whoop/zones/batch` endpoint accepts a comma-separated list of session IDs and queries `WhoopWorkoutCacheRepository.get_by_session_id(sid)` for each. The `get_by_session_id()` method at `/Users/rubertwolff/scratch/rivaflow/rivaflow/db/repositories/whoop_workout_cache_repo.py` line 165 does NOT filter by `user_id` -- it queries `WHERE session_id = ?` only.

**Evidence:**
```python
# whoop_workout_cache_repo.py:170-174
cursor.execute(
    convert_query("SELECT * FROM whoop_workout_cache WHERE session_id = ?"),
    (session_id,),
)
```

**Impact:** An authenticated user could probe arbitrary session IDs and retrieve WHOOP workout data (heart rate zones, strain, calories) belonging to other users. This is an IDOR vulnerability.

**Recommendation:** Add `AND user_id = ?` to the query in `get_by_session_id()`, or verify session ownership in the route handler before returning data.

---

### 1.4 User Data Object Stored in localStorage (LOW)

**Severity:** LOW
**File:** `/Users/rubertwolff/scratch/web/src/contexts/AuthContext.tsx` line 44, 68

**Description:** The full user object (including `email`, `is_admin`, `subscription_tier`) is stored in `localStorage` at line 44 and 68. While this is primarily a convenience cache (the user is re-fetched from the API on mount), it exposes PII to any JavaScript on the page.

**Recommendation:** Remove `localStorage.setItem('user', ...)` and rely on in-memory state only, fetching the user object from `/auth/me` on page load.

---

### 1.5 Access Token Expiry Duration (LOW)

**Severity:** LOW
**File:** `/Users/rubertwolff/scratch/rivaflow/rivaflow/core/settings.py` line 73

**Description:** Default access token expiry is 30 minutes, and refresh token expiry is 30 days. While 30 minutes is acceptable, the 30-day refresh token combined with localStorage storage creates a wide window for token theft.

**Recommendation:** Consider reducing refresh token lifetime to 7 days and implementing refresh token rotation (issue a new refresh token on each refresh, invalidating the old one).

---

## 2. Injection Attacks

### 2.1 SQL Injection -- Dynamic ORDER BY with Whitelist (LOW -- Mitigated)

**Severity:** LOW (properly mitigated)
**Files:**
- `/Users/rubertwolff/scratch/rivaflow/rivaflow/db/repositories/grading_repo.py` lines 52-62
- `/Users/rubertwolff/scratch/rivaflow/rivaflow/db/repositories/friend_repo.py` lines 75-83

**Description:** Several repositories use f-string interpolation for ORDER BY clauses. However, all instances are properly guarded by whitelist validation before interpolation.

**Evidence:**
```python
# grading_repo.py:55-56
if order_by not in GRADING_SORT_OPTIONS:
    order_by = "date_graded DESC"  # Safe default
```

**Assessment:** Properly mitigated. The whitelist pattern is consistently applied.

---

### 2.2 SQL Injection -- Dynamic UPDATE Statements (LOW -- Mitigated)

**Severity:** LOW (properly mitigated)
**Files:**
- `/Users/rubertwolff/scratch/rivaflow/rivaflow/api/routes/admin.py` lines 634-666
- `/Users/rubertwolff/scratch/rivaflow/rivaflow/db/repositories/profile_repo.py` line 213
- `/Users/rubertwolff/scratch/rivaflow/rivaflow/db/repositories/session_repo.py` line 244

**Description:** Multiple repositories dynamically build UPDATE SET clauses using f-strings. However, field names are drawn from hardcoded whitelists (Python dicts or sets), not user input. All VALUES are parameterized with `?` placeholders.

**Evidence:**
```python
# admin.py:635-640
valid_admin_update_fields = {"is_active", "is_admin", "subscription_tier", "is_beta_user"}
for field, value in field_values.items():
    if field not in valid_admin_update_fields:
        raise ValueError(f"Invalid field: {field}")
```

**Assessment:** Properly mitigated. Column names come from whitelists; values are parameterized.

---

### 2.3 No XSS via dangerouslySetInnerHTML (LOW -- Good)

**Severity:** Informational
**Description:** A search for `dangerouslySetInnerHTML`, `v-html`, and `innerHTML` across the entire frontend found zero matches. The React frontend uses JSX text interpolation exclusively, which auto-escapes by default.

---

### 2.4 No Command Injection (LOW -- Good)

**Severity:** Informational
**File:** `/Users/rubertwolff/scratch/rivaflow/verify_no_ai_deps.py` line 24

**Description:** Only one `subprocess.run` call exists in the entire codebase, in a build verification script (not production code). No `os.system`, `os.popen`, or shell=True patterns were found.

---

## 3. API Security

### 3.1 Internal Error Details Leaked in Production Error Responses (HIGH)

**Severity:** HIGH
**CVSS:** 5.3 -- AV:N/AC:L/PR:N/S:U/C:L/I:N/A:N
**Files:**
- `/Users/rubertwolff/scratch/rivaflow/rivaflow/api/routes/analytics.py` (16+ occurrences, e.g., lines 110, 139, 228, 259, 275)
- `/Users/rubertwolff/scratch/rivaflow/rivaflow/api/routes/grapple.py` lines 170-172, 233-234, 246, 258, 276
- `/Users/rubertwolff/scratch/rivaflow/rivaflow/api/routes/admin.py` line 388

**Description:** Numerous route handlers return exception type names and messages directly in HTTP error responses, regardless of environment. While the global `generic_exception_handler` properly hides details in production, many routes catch exceptions and return `detail=f"...error: {type(e).__name__}: {str(e)}"` BEFORE the global handler sees them.

**Evidence:**
```python
# analytics.py:110
detail=f"Analytics error: {type(e).__name__}: {str(e)}"

# grapple.py:170-172
content={"detail": f"Chat error: {type(e).__name__}: {str(e)}"}

# grapple.py:233
detail=f"Failed to create chat session: {type(e).__name__}: {e}"
```

**Impact:** In production, these responses leak internal class names, database error messages, and stack trace fragments. This aids attackers in understanding the technology stack, database structure, and potential attack vectors.

**Recommendation:** Replace all `str(e)` and `type(e).__name__` patterns in HTTP error responses with generic user-facing messages. Log the full details server-side only. Use the existing `handle_service_error()` pattern or the `RivaFlowException` hierarchy consistently.

---

### 3.2 Admin Gym Merge Leaks Exception Details (MEDIUM)

**Severity:** MEDIUM
**File:** `/Users/rubertwolff/scratch/rivaflow/rivaflow/api/routes/admin.py` line 388

**Description:** The gym merge error handler passes `str(e)` directly to the client.

```python
raise ValidationError(f"Failed to merge gyms: {str(e)}")
```

**Recommendation:** Log `str(e)` server-side and return a generic error message.

---

### 3.3 Rate Limiting Inconsistencies (MEDIUM)

**Severity:** MEDIUM
**Files:**
- `/Users/rubertwolff/scratch/rivaflow/rivaflow/api/routes/social.py` lines 90, 200-220, 283-340, 317-340
- Various routes without rate limiting

**Description:** Rate limiting is applied inconsistently:
- `unfollow_user` (line 90) has no rate limit
- `unlike_activity` (line 200) has no rate limit
- `delete_comment` (line 317) has no rate limit
- `update_comment` (line 283) has no rate limit
- All notification mark-as-read endpoints lack rate limiting

While these are lower-risk endpoints, an attacker could abuse unrate-limited DELETE endpoints to cause excessive database operations.

**Recommendation:** Apply rate limiting to all write endpoints, especially DELETE operations.

---

### 3.4 Grapple Rate Limiter Fails Open (MEDIUM)

**Severity:** MEDIUM
**File:** `/Users/rubertwolff/scratch/rivaflow/rivaflow/api/routes/grapple.py` lines 190-193

**Description:** When the Grapple rate limiter fails (e.g., Redis/database error), it fails open -- allowing the request through:

```python
except (ConnectionError, OSError) as e:
    # Fail open -- allow the request if rate limiting is broken
    rate_check = {"allowed": True, "remaining": 99, "limit": 99}
```

**Impact:** If the rate limit storage becomes unavailable, users can send unlimited messages to LLM providers, potentially causing runaway costs.

**Recommendation:** Implement a fallback in-memory rate limiter, or fail closed when the cost implications are significant. At minimum, add monitoring/alerting when the rate limiter fails.

---

### 3.5 Weak Password Requirements (MEDIUM)

**Severity:** MEDIUM
**File:** `/Users/rubertwolff/scratch/rivaflow/rivaflow/core/services/auth_service.py` line 77

**Description:** Password validation only checks `len(password) < 8`. There are no requirements for:
- Uppercase/lowercase mix
- Numeric characters
- Special characters
- Common password blocklist (e.g., "password123")

**Recommendation:** Implement a password strength checker that requires at least 10 characters with a mix of character types, or use a library like `zxcvbn` for strength scoring. Block the top 10,000 common passwords.

---

## 4. Data Protection

### 4.1 Password Hashing (GOOD)

**Severity:** Informational
**File:** `/Users/rubertwolff/scratch/rivaflow/rivaflow/core/auth.py` lines 12, 33-45

**Description:** Passwords are hashed with bcrypt via `passlib.context.CryptContext`. The 72-byte bcrypt limit is properly handled with truncation. This is industry-standard.

---

### 4.2 WHOOP OAuth Token Encryption (GOOD)

**Severity:** Informational
**File:** `/Users/rubertwolff/scratch/rivaflow/rivaflow/core/utils/encryption.py`

**Description:** WHOOP OAuth tokens are encrypted at rest using Fernet (AES-128-CBC with HMAC-SHA256). The encryption key is loaded from `WHOOP_ENCRYPTION_KEY` environment variable. Proper error handling for missing keys and decryption failures.

---

### 4.3 User Training Data Sent to External LLM Services (MEDIUM)

**Severity:** MEDIUM
**Files:**
- `/Users/rubertwolff/scratch/rivaflow/rivaflow/core/services/grapple/context_builder.py`
- `/Users/rubertwolff/scratch/rivaflow/rivaflow/api/routes/transcribe.py` lines 100-106, 131-143

**Description:** The Grapple AI Coach sends user training data (session history, readiness scores, gradings, profile info) to external LLM providers (Groq, Together AI). The transcription endpoint sends audio files to OpenAI's Whisper API and text to GPT-4o-mini. While this is core functionality, users should be informed about:
- What data is shared with which providers
- Data retention policies of each provider
- Whether users can opt out of AI features while retaining other functionality

**Recommendation:** Add a privacy disclosure in the UI for AI features. Ensure LLM provider agreements include data processing addendums. Consider offering an opt-out toggle.

---

### 4.4 Sentry PII Configuration (GOOD)

**Severity:** Informational
**File:** `/Users/rubertwolff/scratch/rivaflow/rivaflow/api/main.py` line 89

**Description:** Sentry is configured with `send_default_pii=False`, which prevents automatic PII collection. This is correct.

---

## 5. Frontend Security

### 5.1 Content Security Policy (GOOD, with Note)

**Severity:** Informational
**File:** `/Users/rubertwolff/scratch/rivaflow/rivaflow/api/middleware/security_headers.py` lines 49-59

**Description:** The CSP policy is restrictive (`default-src 'self'`, `script-src 'self'`, `frame-ancestors 'none'`). However, `style-src 'self' 'unsafe-inline'` allows inline styles, and `img-src 'self' data: https:` allows loading images from any HTTPS origin.

**Recommendation:** Replace `'unsafe-inline'` in `style-src` with nonce-based or hash-based CSP if possible. Restrict `img-src` to specific trusted domains (e.g., your S3/R2 bucket).

---

### 5.2 CSP Applied to API Responses Only (MEDIUM)

**Severity:** MEDIUM
**Files:**
- `/Users/rubertwolff/scratch/rivaflow/rivaflow/api/middleware/security_headers.py`
- `/Users/rubertwolff/scratch/render.yaml` lines 63-69

**Description:** The CSP headers are set by the backend SecurityHeadersMiddleware. However, the frontend is deployed as a separate Render static site (`rivaflow-web`), which only has `X-Frame-Options` and `X-Content-Type-Options` headers configured in `render.yaml`. The CSP, HSTS, Referrer-Policy, and Permissions-Policy headers are **missing** from the static frontend site.

**Evidence:**
```yaml
# render.yaml:63-69
headers:
  - path: /*
    name: X-Frame-Options
    value: DENY
  - path: /*
    name: X-Content-Type-Options
    value: nosniff
```

**Recommendation:** Add the full security header suite to the Render static site configuration in `render.yaml`, including:
- `Strict-Transport-Security: max-age=31536000; includeSubDomains`
- `Content-Security-Policy` (tailored for the React SPA)
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy` (disable unused features)

---

## 6. Secrets & Configuration

### 6.1 Production SECRET_KEY Enforcement (GOOD)

**Severity:** Informational
**File:** `/Users/rubertwolff/scratch/rivaflow/rivaflow/core/auth.py` lines 19-26

**Description:** The application raises a `RuntimeError` at startup if a weak SECRET_KEY is detected in production (less than 32 characters or starts with "dev-"). This is an excellent safeguard.

---

### 6.2 No Hardcoded Secrets Found (GOOD)

**Severity:** Informational

**Description:** A comprehensive search for hardcoded API keys, passwords, and secrets found only test fixtures and documentation examples. No production secrets are committed.

---

### 6.3 .gitignore Coverage (GOOD, with Note)

**Severity:** LOW
**File:** `/Users/rubertwolff/scratch/.gitignore`

**Description:** The `.gitignore` properly excludes `.env`, `*.db`, `uploads/`, and `rivaflow_export_*.json`. However, `backend.log` is present in the repo root. While `*.log` is in `.gitignore`, this file may have been committed before the rule was added.

**Recommendation:** Verify `backend.log` is not tracked by git (`git ls-files backend.log`). If tracked, remove it from the index.

---

### 6.4 Database Export Files in Repo Root (LOW)

**Severity:** LOW
**File:** `/Users/rubertwolff/scratch/` (root directory)

**Description:** Three `rivaflow_export_*.json` files exist in the repo root. While `.gitignore` excludes them from git, their presence on the development machine may contain user PII (training sessions, personal data). These should be stored in a secure, non-root location.

---

### 6.5 Render Database IP Allow List Empty (LOW)

**Severity:** LOW
**File:** `/Users/rubertwolff/scratch/render.yaml` line 83

**Description:** `ipAllowList: []` means the PostgreSQL database accepts connections from any IP (relying solely on username/password authentication). While Render provides network-level protection, an explicit IP allowlist adds defense-in-depth.

**Recommendation:** Restrict `ipAllowList` to the API service's IP range.

---

## 7. IDOR & Authorization Bypass

### 7.1 WHOOP Zones Batch -- No User Ownership Check (HIGH -- see 1.3)

Already documented in Section 1.3.

---

### 7.2 WHOOP Session Context -- Session Ownership Verified (GOOD)

**File:** `/Users/rubertwolff/scratch/rivaflow/rivaflow/api/routes/integrations.py` line 282

**Description:** `SessionRepository.get_by_id(user_id, session_id)` includes `user_id` in the query. Properly protected.

---

### 7.3 Social Likes/Comments -- Activity Ownership Not Verified for Reads (LOW)

**Severity:** LOW
**File:** `/Users/rubertwolff/scratch/rivaflow/rivaflow/api/routes/social.py` lines 223-243, 343-363

**Description:** The `get_activity_likes` and `get_activity_comments` endpoints accept `activity_type` and `activity_id` but do not verify that the requesting user has permission to view that activity. Any authenticated user can retrieve likes/comments for any activity ID.

**Impact:** Low -- likes and comments are inherently social data. However, for private activities (visibility_level='private'), this leaks information that the activity exists and has social interactions.

**Recommendation:** Verify that the activity's `visibility_level` allows viewing by the requesting user, or that the requesting user is the activity owner.

---

### 7.4 All Session Routes Properly Filter by user_id (GOOD)

**Description:** Session CRUD operations consistently use `user_id=current_user["id"]` in queries. The session repository's `get_by_id`, `update`, and `delete` methods all include `WHERE user_id = ?` conditions.

---

### 7.5 Admin Routes Properly Protected (GOOD)

**Description:** All admin routes use `Depends(require_admin)` or `Depends(get_admin_user)`, which enforces the `is_admin` flag. Admin cannot delete their own account (line 696). Audit logging captures all admin actions.

---

## 8. CORS Configuration

### 8.1 CORS Configuration (GOOD)

**Severity:** Informational
**File:** `/Users/rubertwolff/scratch/rivaflow/rivaflow/api/main.py` lines 126-158

**Description:** CORS is properly configured:
- Production uses `ALLOWED_ORIGINS` environment variable (comma-separated whitelist)
- Development defaults to localhost ports only
- Methods restricted to necessary HTTP verbs
- Headers restricted to `Content-Type` and `Authorization`
- Preflight caching enabled (1 hour)

---

## 9. Dependency Vulnerabilities

### 9.1 jose Library (Informational)

**File:** `/Users/rubertwolff/scratch/rivaflow/rivaflow/core/auth.py` line 7

**Description:** The `python-jose` library is used for JWT operations. It is a well-maintained library but has had occasional CVEs. Ensure it is regularly updated.

**Recommendation:** Run `pip-audit` or `safety check` regularly in CI. Consider `PyJWT` as an alternative if `python-jose` becomes unmaintained.

---

### 9.2 API Documentation Disabled in Production (GOOD)

**File:** `/Users/rubertwolff/scratch/rivaflow/rivaflow/api/main.py` lines 102-104

**Description:** Swagger/ReDoc documentation and OpenAPI schema are properly disabled in production:
```python
_docs_url = None if settings.IS_PRODUCTION else "/docs"
_redoc_url = None if settings.IS_PRODUCTION else "/redoc"
_openapi_url = None if settings.IS_PRODUCTION else "/openapi.json"
```

---

## 10. Additional Findings

### 10.1 Webhook Signature Verification Bypassed When Secret Missing (HIGH)

**Severity:** HIGH
**CVSS:** 7.5 -- AV:N/AC:L/PR:N/S:U/C:N/I:H/A:N
**File:** `/Users/rubertwolff/scratch/rivaflow/rivaflow/api/routes/webhooks.py` lines 73-82

**Description:** The WHOOP webhook endpoint skips signature verification entirely when `WHOOP_CLIENT_SECRET` is not set:

```python
if secret:
    # ... verify signature
else:
    logger.warning("WHOOP_CLIENT_SECRET not set -- skipping signature check")
```

**Impact:** If the `WHOOP_CLIENT_SECRET` environment variable is accidentally removed or not configured, the webhook endpoint becomes completely unauthenticated. An attacker could send forged webhook payloads to trigger data syncs, create fake sessions, or manipulate user data.

**Recommendation:** If `WHOOP_CLIENT_SECRET` is not set, reject ALL webhook requests with 503 Service Unavailable. Never silently skip signature verification.

---

### 10.2 Health Check Endpoint Exposes Database Type (LOW)

**Severity:** LOW
**Files:**
- `/Users/rubertwolff/scratch/rivaflow/rivaflow/api/main.py` lines 283-319
- `/Users/rubertwolff/scratch/rivaflow/rivaflow/api/routes/health.py`

**Description:** The health check endpoint at `/health` returns database connectivity status including error type names (`type(e).__name__`). While health endpoints are commonly exposed, the error details help fingerprint the database technology.

**Recommendation:** Return only `"database": "ok"` or `"database": "error"` without type information.

---

### 10.3 convert_query() Function Safety (GOOD, with Caveat)

**Severity:** Informational
**File:** `/Users/rubertwolff/scratch/rivaflow/rivaflow/db/database.py` lines 25-38

**Description:** The `convert_query()` function performs a simple `?` to `%s` replacement for PostgreSQL. This is safe because:
1. All `?` placeholders are parameterized (values are never interpolated into the query string)
2. The conversion only changes placeholder syntax, not query structure

**Caveat:** If any query string contained literal `?` characters (e.g., in a LIKE pattern), they would be incorrectly converted. However, no such patterns were found in the codebase.

---

### 10.4 Broadcast Email -- No Confirmation Step (LOW)

**Severity:** LOW
**File:** `/Users/rubertwolff/scratch/rivaflow/rivaflow/api/routes/admin.py` lines 1080-1128

**Description:** The admin broadcast email endpoint sends to ALL active users immediately in a background thread with no confirmation step, preview, or undo capability. A misclick or crafted request could send an unintended email to all users.

**Recommendation:** Add a two-step flow: (1) preview with recipient count, (2) confirm with a nonce token. Rate limit to 1/hour maximum.

---

## Summary of Recommendations (Priority Order)

| Priority | Finding | Severity | Section |
|----------|---------|----------|---------|
| P0 | Webhook signature bypass when secret missing | HIGH | 10.1 |
| P0 | Error details leaked in production responses | HIGH | 3.1 |
| P1 | JWT tokens in localStorage (migrate to httpOnly cookies) | HIGH | 1.1 |
| P1 | WHOOP zones batch IDOR (no user_id filter) | MEDIUM | 1.3 |
| P1 | CSP/HSTS missing from frontend static site | MEDIUM | 5.2 |
| P2 | Grapple rate limiter fails open | MEDIUM | 3.4 |
| P2 | Weak password requirements | MEDIUM | 3.5 |
| P2 | Rate limiting inconsistencies on write endpoints | MEDIUM | 3.3 |
| P2 | WHOOP callback URL parameter not sanitized | MEDIUM | 1.2 |
| P2 | User data sent to LLM providers without disclosure | MEDIUM | 4.3 |
| P2 | Admin gym merge leaks exception details | MEDIUM | 3.2 |
| P3 | Social endpoints expose private activity metadata | LOW | 7.3 |
| P3 | User object cached in localStorage | LOW | 1.4 |
| P3 | Access/refresh token lifetimes | LOW | 1.5 |
| P3 | Database export files in repo root | LOW | 6.4 |
| P3 | Database IP allowlist empty | LOW | 6.5 |
| P3 | Health check exposes database type | LOW | 10.2 |
| P3 | Broadcast email no confirmation step | LOW | 10.4 |

---

## Positive Security Practices Observed

1. **Bcrypt password hashing** with proper 72-byte truncation handling
2. **Parameterized SQL queries** throughout all repositories (no string interpolation of values)
3. **SQL ORDER BY whitelist** pattern consistently applied
4. **Admin role enforcement** via FastAPI dependency injection with audit logging
5. **CSRF protection** for WHOOP OAuth via single-use, time-limited state tokens
6. **Fernet encryption** for WHOOP OAuth tokens at rest
7. **Rate limiting** on authentication endpoints (5/min login, 5/min register, 3/hr forgot-password)
8. **User enumeration prevention** (forgot-password always returns success)
9. **Production secret key enforcement** (startup check for minimum length)
10. **Security headers middleware** (HSTS, X-Frame-Options, CSP, Permissions-Policy)
11. **Swagger/ReDoc disabled in production**
12. **Sentry PII disabled** (`send_default_pii=False`)
13. **File upload validation** with magic byte checking (not just extension)
14. **Session ownership checks** (user_id filtering in all session queries)
15. **CORS whitelist** (not wildcard) with restricted methods and headers
16. **Error handler** sanitizes sensitive fields (password, token) from validation errors
17. **Password reset token single-use** with expiry and rate limiting
18. **All refresh tokens invalidated** on password reset (forced re-login)
