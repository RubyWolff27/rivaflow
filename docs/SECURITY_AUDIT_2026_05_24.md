# Security audit followups — 2026-05-24

Following the joint Sage + Groot codebase review on 2026-05-24, this document records the immediate code-level remediation that landed in PR `security/audit-followups-2026-05-24`.

## Findings addressed

### 1. `/health` endpoint disclosure (Groot finding, audit report 2026-05-24T12:14)

**Problem:** Public `/health` returned:

```json
{
  "status": "healthy",
  "service": "rivaflow-api",
  "version": "0.5.0",
  "commit": "<git sha>",
  "email": {"enabled": true, "method": "sendgrid"},
  "database": "connected"
}
```

Anyone reaching the public URL could enumerate version, commit, email provider, and DB state — useful for legitimate monitoring, but also a free reconnaissance surface for attackers.

**Fix:** `rivaflow/api/routes/health.py` — public `/health` now returns `{"status": "healthy"}` only. Internal DB check still propagates 503 to load balancers and Render.

Detailed health is moved to `/health/detailed`, gated by `X-Admin-Token` matching the `HEALTH_DETAILED_TOKEN` environment variable. Returns 404 (not 401/403) when missing/wrong to conceal endpoint existence from unauthenticated probes.

### 2. GitLeaks findings classification (Groot audit 2026-05-24T12:13)

GitLeaks found 14 historical findings in `rivaflow`, all classified by Sage:

| File | Lines | Classification |
|---|---|---|
| `rivaflow/docs/api-reference.md` | 47, 48, 85, 86, 108, 115 | Documentation JWT examples (placeholders, prefix `eyJ0eXAiOiJKV1QiLCJhbGc...`) |
| `rivaflow/CHAT_RUNBOOK.md` | 88, 117, 123, 337 | History-only (file no longer in HEAD) |
| `tests/test_email_service.py` | 34 | Test placeholder `SG.test-key-123` |
| `tests/test_security.py` | 173 | Test JWT pattern check |
| `rivaflow/TEST_FAILURE_FIX_PLAN.md` | 89 | History-only |
| `rivaflow/tests/unit/test_security.py` | 164 | Test JWT pattern check |

**Conclusion:** No live secrets in HEAD. History-only residue in 2 deleted files is non-rotating cost (placeholders, not real secrets).

**No action needed** beyond this classification record. If a true secret is ever flagged in future scans, rotate the credential immediately and use `git filter-repo` to scrub.

## Followups not in this PR (separate work)

- **Sentry DSN environment variable** — SDK is wired (`api/main.py:120`) but `SENTRY_DSN` not set on Render → events not flowing. Add the env var after creating Sentry project.
- **Render health check path** — Render's rivaflow-api-v2 has empty health check path. Setting to `/health/live` is recommended (no DB roundtrip, fast probe).
- **Duplicate `web/` vs `rivaflow/web/` trees** — Groot flagged this as a future sync foot-gun. Top-level `/web/` is the duplicate; canonical is `rivaflow/web/` per Render config. To be consolidated in a separate PR after deploy-path verification.
- **Postgres HA / multi-region** — `rivaflow-db-v2` is `basic_256mb`, single Singapore region, no HA, no read replicas. Single-point-of-failure. Upgrade path: Render's `standard_1gb` plan + replica when traffic warrants.

## Related

- Groot review bridge note: `~/.claude/MEMORY/bridge/from-groot/20260524-092527-codebase-review-groot.md`
- Groot Render audit: `~/.claude/MEMORY/bridge/from-groot/20260524-121431-render-branch-audit.md`
- Groot GitLeaks audit: `~/.claude/MEMORY/bridge/from-groot/20260524-121333-gitleaks-audit.md`
- Sage access policy: `~/.claude/projects/-Users-rubertwolff/memory/reference_groot_access_policy.md`
