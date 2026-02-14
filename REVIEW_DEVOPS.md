# RivaFlow DevOps & Infrastructure Review

**Reviewed:** 2026-02-11
**Reviewer:** Claude Opus 4.6 (automated)
**Scope:** CI/CD, Render config, dependencies, secrets, database, monitoring, reliability

---

## CRITICAL

### C1. CI uses PostgreSQL 16 but production runs PostgreSQL 18

- **File:** `/Users/rubertwolff/scratch/.github/workflows/test.yml` (line 21)
- **File:** `/Users/rubertwolff/scratch/render.yaml` (line 77-83)
- CI runs `postgres:16` in the service container. Render provisions PostgreSQL 18.
- This means tests never exercise PG 18-specific behaviour or catch regressions from deprecated PG 16 features.
- **Fix:** Change the CI service image to `postgres:18` (or at minimum `postgres:17`) to match production.

### C2. Database is publicly accessible (empty ipAllowList)

- **File:** `/Users/rubertwolff/scratch/render.yaml` (line 83)
- `ipAllowList: []` means the PostgreSQL database accepts connections from **any IP** on the internet.
- Anyone who obtains (or brute-forces) the credentials can connect directly.
- **Fix:** Restrict `ipAllowList` to the Render service IPs or internal network. Render supports `0.0.0.0/0` (current, wide-open) vs specific CIDR ranges. At minimum use Render's internal connection string (`connectionString` property already used) and set `ipAllowList` to block external access.

### C3. `python-jose` is unmaintained and has known CVEs

- **File:** `/Users/rubertwolff/scratch/rivaflow/requirements.txt` (line 14)
- **File:** `/Users/rubertwolff/scratch/pyproject.toml` (line 33)
- `python-jose==3.5.0` has not been updated since 2022. Its `ecdsa` dependency has CVE-2024-23342 (already being suppressed in `security.yml`). The project is effectively abandoned.
- **Fix:** Migrate to `PyJWT` (actively maintained, used by major frameworks) or `joserfc`. This removes the need to suppress CVE-2024-23342 and the `ecdsa` transitive dependency entirely.

### C4. Dual migration path creates risk of schema drift

- **File:** `/Users/rubertwolff/scratch/rivaflow/rivaflow/db/database.py` (lines 421-578) -- `_apply_migrations()`
- **File:** `/Users/rubertwolff/scratch/rivaflow/rivaflow/db/migrate.py` (lines 117-191) -- `run_migrations()`
- **File:** `/Users/rubertwolff/scratch/start.sh` (lines 23-33)
- Production runs migrations THREE times at startup:
  1. `start.sh` line 25: `init_db()` (creates tracking table, skips `_apply_migrations` for PG)
  2. `start.sh` line 33: `python rivaflow/db/migrate.py` (calls `_apply_migrations` via `run_migrations()`)
  3. `main.py` line 181-189: `startup_event` also calls `run_migrations()` again
- While the advisory lock and idempotency checks prevent double-application, running migrations three times per deploy is wasteful and adds startup latency. If `migrate.py` partially fails, the app might still start with an inconsistent schema since `main.py` catches and re-raises but `start.sh` uses `set -e`.
- The hard-coded migration list in `_apply_migrations()` must be manually kept in sync -- there is no auto-discovery.
- **Fix:** Pick ONE migration entry point. Remove the duplicate call in either `start.sh` or `main.py` startup event. Consider auto-discovering migration files instead of maintaining a hard-coded list.

---

## HIGH

### H1. Render deploy step is a no-op (relies entirely on auto-deploy)

- **File:** `/Users/rubertwolff/scratch/.github/workflows/deploy.yml` (lines 59-64)
- The "Trigger Render deployment" step literally prints `echo "Render will auto-deploy from main branch"`. There is no actual deploy trigger.
- Since `autoDeploy: true` is set in `render.yaml`, Render deploys on every push to `main` **independently** of whether CI passes. The `deploy.yml` workflow runs tests then waits 60 seconds and checks health, but Render may have already started or finished deploying before CI even completes.
- This means: broken code pushed to `main` **will deploy** even if tests fail. The CI "gate" is an illusion.
- **Fix:** Either:
  - (A) Set `autoDeploy: false` in `render.yaml` and use the Render Deploy Hook or API in the `deploy.yml` step (after tests pass), or
  - (B) Use GitHub branch protection rules to require the `Tests` workflow to pass before merge to `main`.

### H2. No uvicorn workers -- single process serves all traffic

- **File:** `/Users/rubertwolff/scratch/start.sh` (line 37-40)
- Uvicorn runs with `--host 0.0.0.0 --port $PORT` but no `--workers` flag. This means a single process handles all requests.
- On the Render `starter` plan, this is likely fine for beta. But as traffic grows, a single worker is a bottleneck and a single unhandled sync call can block the event loop.
- **Fix:** Add `--workers 2` (or use gunicorn with uvicorn workers: `gunicorn rivaflow.api.main:app -k uvicorn.workers.UvicornWorker -w 2`). Note: APScheduler jobs will run in every worker -- add a guard or use a single-leader pattern.

### H3. Dependency version drift between pyproject.toml files and requirements.txt

- **File:** `/Users/rubertwolff/scratch/pyproject.toml` (root)
- **File:** `/Users/rubertwolff/scratch/rivaflow/pyproject.toml` (inner)
- **File:** `/Users/rubertwolff/scratch/rivaflow/requirements.txt`
- Three different dependency manifests with conflicting versions:
  - `fastapi`: root=`0.128.0`, inner=`0.128.4`, requirements.txt=`0.128.4`
  - `pydantic`: root=`2.10.3`, inner=`2.12.5`, requirements.txt=`2.12.5`
  - `pydantic-settings`: root=`2.6.1`, inner=`2.12.0`, requirements.txt=`2.12.0`
  - `typer`: root=`0.15.1`, inner=`0.21.1`, requirements.txt=`0.21.1`
  - `psycopg2-binary`: root=`2.9.10`, inner=`2.9.11`, requirements.txt=`2.9.11`
  - `redis`: root=`5.2.1`, inner=`5.3.1`, requirements.txt=`5.3.1`
  - `sendgrid`: root=`6.11.0`, inner=`6.12.5`, requirements.txt=`6.12.5`
  - `pgvector`: root=`0.3.6`, inner=`0.4.2`, requirements.txt=`0.4.2`
  - `python-dotenv`: root=`1.1.0`, inner=`1.2.1`, requirements.txt=`1.2.1`
  - `boto3`: only in requirements.txt, missing from both pyproject.toml
  - `sentry-sdk`: only in requirements.txt, missing from both pyproject.toml
  - `apscheduler`: only in requirements.txt, missing from both pyproject.toml
- CI installs from `pip install -e rivaflow/` (uses inner pyproject.toml) but Render builds from `pip install -r rivaflow/requirements.txt`. Root pyproject.toml is stale and unused in production.
- **Fix:** Consolidate to a single source of truth. Either use requirements.txt exclusively (production pattern) or generate it from pyproject.toml. Delete or clearly mark the root `pyproject.toml` dependencies as "dev/local only". Add `boto3`, `sentry-sdk`, and `apscheduler` to the inner pyproject.toml.

### H4. render.yaml says frontend region is "singapore" but MEMORY.md says "global"

- **File:** `/Users/rubertwolff/scratch/render.yaml` (line 58)
- The static site `rivaflow-web` has `region: singapore`. For a static site, Render serves from its CDN regardless, but having the build region set to Singapore means builds happen in Singapore.
- This is minor for build performance but the configuration does not match the stated intent of "global" distribution.
- **Fix:** Verify the actual Render dashboard setting. Static sites on Render are served globally via CDN regardless of region, so this is mostly cosmetic. Update MEMORY.md or render.yaml to match reality.

### H5. `@app.on_event("startup")` and `@app.on_event("shutdown")` are deprecated

- **File:** `/Users/rubertwolff/scratch/rivaflow/rivaflow/api/main.py` (lines 171, 210)
- FastAPI deprecated `on_event` in favour of the `lifespan` context manager (since FastAPI 0.93+). Current FastAPI version is 0.128.x. While still functional, these will be removed in a future version.
- **Fix:** Migrate to the `lifespan` async context manager pattern:
  ```python
  @asynccontextmanager
  async def lifespan(app: FastAPI):
      # startup logic
      yield
      # shutdown logic

  app = FastAPI(lifespan=lifespan)
  ```

### H6. `datetime.utcnow()` usage throughout codebase (deprecated in Python 3.12+)

- **Files:** Multiple files (auth.py, admin_grapple.py, notification_repo.py, refresh_token_repo.py, waitlist_repo.py, chat_session_repo.py)
- `datetime.utcnow()` is deprecated since Python 3.12. It returns a naive datetime that can cause subtle timezone bugs.
- **Fix:** Replace with `datetime.now(datetime.timezone.utc)` across the codebase.

### H7. APScheduler uses SQLite date functions in PostgreSQL context

- **File:** `/Users/rubertwolff/scratch/rivaflow/rivaflow/core/scheduler.py` (lines 29-32, 60-62, 119-126)
- The scheduler jobs use `date('now', '-14 days')` and `date('now', ?)` which are SQLite date functions. The `convert_query()` call only converts `?` to `%s` -- it does NOT convert SQLite date functions to PostgreSQL equivalents.
- In production (PostgreSQL), `date('now', '-14 days')` will fail or produce unexpected results because PostgreSQL's `date()` function has different semantics.
- **Fix:** Use database-agnostic date arithmetic: `CURRENT_DATE - INTERVAL '14 days'` for PostgreSQL, or use `convert_query()` to also handle date function translation.

---

## MEDIUM

### M1. No Codecov token configured -- coverage upload silently fails

- **File:** `/Users/rubertwolff/scratch/.github/workflows/test.yml` (lines 64-69)
- The `codecov/codecov-action@v5` step runs but without a token, uploads fail. This has been a known issue per MEMORY.md.
- **Fix:** Either configure the Codecov token as a repository secret, or remove the step to avoid noisy CI logs.

### M2. Frontend build runs `tsc && vite build` without a lint step

- **File:** `/Users/rubertwolff/scratch/web/package.json` (line 8)
- The build command runs TypeScript compilation then Vite build. There is no ESLint or Prettier check for the frontend code. CI runs `type-check` and `build` but no frontend linter.
- **Fix:** Add an ESLint configuration and run it in CI alongside the TypeScript check.

### M3. `@types/react-window` is in `dependencies` instead of `devDependencies`

- **File:** `/Users/rubertwolff/scratch/web/package.json` (line 15)
- Type definition packages are build-time only and should be in `devDependencies`.
- **Fix:** Move `@types/react-window` to `devDependencies`.

### M4. No structured/JSON logging for production

- **File:** `/Users/rubertwolff/scratch/rivaflow/rivaflow/api/main.py` (lines 74-79)
- Logging uses `basicConfig` with a plain text format. In production on Render, this makes log aggregation, searching, and alerting harder.
- Sentry is configured but optional (requires `SENTRY_DSN` env var and the SDK is imported with a try/except).
- **Fix:** Add JSON structured logging for production (e.g., `python-json-logger` or `structlog`). This enables better log parsing in Render's log viewer and any future log aggregation service.

### M5. CSP header on API restricts `connect-src` to `'self'`

- **File:** `/Users/rubertwolff/scratch/rivaflow/rivaflow/api/middleware/security_headers.py` (lines 49-59)
- The Content-Security-Policy sets `connect-src 'self'` which would block the frontend from making API calls to a different subdomain. However, since the frontend is a separate static site on a different domain (`rivaflow.app` vs `api.rivaflow.app`), the CSP on the API is only relevant if the API serves HTML -- which it does when the React build is co-located.
- The CSP is applied to ALL responses including JSON API responses, where it is unnecessary overhead.
- **Fix:** Only apply CSP to HTML responses, or adjust `connect-src` to include `https://api.rivaflow.app` if the frontend is served from the API.

### M6. Backup strategy is manual only

- **File:** `/Users/rubertwolff/scratch/scripts/backup_db.sh`
- The backup script must be run manually from a local machine with `pg_dump` and the `DATABASE_URL`. There is no automated/scheduled backup.
- Render's paid database plans include automated daily backups, but the `starter` plan may have limited backup features.
- **Fix:** Verify Render's backup policy for the `starter` plan. Consider a scheduled GitHub Action or cron job to run the backup script automatically. Store backups in S3/R2 rather than locally.

### M7. Connection pool maxconn=40 may be too high for Render starter plan

- **File:** `/Users/rubertwolff/scratch/rivaflow/rivaflow/db/database.py` (line 114)
- The PostgreSQL connection pool is set to `maxconn=40`. Render's starter PostgreSQL plan typically allows fewer concurrent connections (often 20-25 for starter plans).
- If the pool tries to open more connections than the database allows, requests will fail with "too many connections" errors.
- **Fix:** Check the actual connection limit on the Render database (`SHOW max_connections;`). Set `maxconn` to be safely below that limit (e.g., 80% of `max_connections` minus connections reserved for superuser).

### M8. Health check in deploy.yml has a naive 60-second sleep

- **File:** `/Users/rubertwolff/scratch/.github/workflows/deploy.yml` (lines 68-69)
- The deploy workflow does `sleep 60` then checks health. If the deploy takes longer, the check passes against the OLD deployment. If it takes less time, it wastes CI minutes.
- **Fix:** Implement a polling loop that checks health every 10 seconds for up to 5 minutes, breaking on success.

### M9. Smoke test does not fail the workflow on DB health check failure

- **File:** `/Users/rubertwolff/scratch/.github/workflows/deploy.yml` (lines 83-93)
- The DB health check in the smoke test prints "Database health check failed" but does not `exit 1`, so the workflow reports success even if the database is down.
- **Fix:** Add `exit 1` after the failure message.

### M10. TruffleHog pinned to `@main` -- unstable and unpredictable

- **File:** `/Users/rubertwolff/scratch/.github/workflows/security.yml` (line 61)
- `uses: trufflesecurity/trufflehog@main` pins to the latest commit on `main`. This means builds can break without any code change, and you lose reproducibility.
- **Fix:** Pin to a specific version tag (e.g., `trufflesecurity/trufflehog@v3.x.x`).

---

## LOW

### L1. Dual web/ directory pattern is fragile

- CI has a sync check (`diff -r rivaflow/web/src web/src`) in `test.yml` (lines 102-106), which is good.
- However, the workflow only checks `src/` and `package.json`, not other files like `index.html`, `tailwind.config.js`, `tsconfig.json`, `vite.config.ts`, `postcss.config.js`, or `.env.production`.
- **Fix:** Extend the diff check to cover all relevant files, or better yet, eliminate the dual directory by having `web/` be a symlink or using a build-time copy step.

### L2. Root pyproject.toml `[tool.black]` line-length=88 vs inner line-length=100

- **File:** `/Users/rubertwolff/scratch/pyproject.toml` (line 79) -- `line-length = 88`
- **File:** `/Users/rubertwolff/scratch/rivaflow/pyproject.toml` (line 134) -- `line-length = 100`
- CI runs `black --check rivaflow/ tests/` from the repo root, which picks up the root config (line-length=88). Running `python -m black` from inside `rivaflow/` picks up line-length=100.
- This is documented in MEMORY.md and developers know the rule, but it remains a footgun for new contributors.
- **Fix:** Remove the `[tool.black]` section from the inner pyproject.toml to avoid confusion, or add a comment explaining the intentional override.

### L3. `serve` package in production dependencies

- **File:** `/Users/rubertwolff/scratch/web/package.json` (line 24)
- `serve` (a local static file server) is in `dependencies`. It is only used for local previewing and is never used in production (Render serves static files directly).
- **Fix:** Move to `devDependencies` to reduce the production install footprint.

### L4. Hardcoded API version "0.2.0" in multiple places

- **File:** `/Users/rubertwolff/scratch/rivaflow/rivaflow/api/main.py` (line 109)
- **File:** `/Users/rubertwolff/scratch/rivaflow/rivaflow/api/routes/health.py` (line 33)
- The version string "0.2.0" is hardcoded, while `pyproject.toml` says "0.5.0". These will drift further over time.
- **Fix:** Read version from a single source of truth (e.g., the `VERSION` file at `rivaflow/rivaflow/VERSION`, or `importlib.metadata.version("rivaflow")`).

### L5. `apscheduler>=3.10,<4` is not pinned to an exact version

- **File:** `/Users/rubertwolff/scratch/rivaflow/requirements.txt` (line 37)
- All other dependencies are pinned exactly (e.g., `fastapi==0.128.4`). APScheduler uses a range constraint, which means different installs can get different versions.
- **Fix:** Pin to a specific version for reproducible builds (e.g., `apscheduler==3.10.4`).

### L6. Security scan suppresses CVE-2024-23342 indefinitely

- **File:** `/Users/rubertwolff/scratch/.github/workflows/security.yml` (line 35)
- The `--ignore-vuln CVE-2024-23342` flag will suppress this CVE forever, even if a fix becomes available.
- **Fix:** Add a comment with a review date. Better yet, migrate away from `python-jose` (see C3) which removes the `ecdsa` dependency entirely.

### L7. Dependabot ignores all major version updates for Python dependencies

- **File:** `/Users/rubertwolff/scratch/.github/dependabot.yml` (lines 21-22)
- This is a reasonable safety measure but means major security fixes that bump major versions will be silently ignored.
- **Fix:** Periodically review ignored major versions manually (quarterly).

### L8. `web/dist/` and `web/node_modules/` are committed or present in repo

- **File:** `/Users/rubertwolff/scratch/web/dist/` and `/Users/rubertwolff/scratch/web/node_modules/` directories exist locally
- The `.gitignore` covers `web/dist/` but not `rivaflow/web/dist/` or `rivaflow/web/node_modules/`.
- The root `node_modules/` directory also exists (line 61 of listing).
- **Fix:** Verify these are all properly gitignored. Add `rivaflow/web/dist/` and `rivaflow/web/node_modules/` and `node_modules/` to `.gitignore` if not already covered.

### L9. Custom gzip middleware instead of using FastAPI/Starlette built-in

- **File:** `/Users/rubertwolff/scratch/rivaflow/rivaflow/api/middleware/compression.py`
- FastAPI/Starlette provides `GZipMiddleware` out of the box (`from starlette.middleware.gzip import GZipMiddleware`). The custom implementation buffers the entire response body in memory before compressing, which is less efficient for large responses.
- **Fix:** Replace with the built-in `GZipMiddleware(app, minimum_size=1000)`.

### L10. `Permissions-Policy` header disables microphone but app has voice transcription

- **File:** `/Users/rubertwolff/scratch/rivaflow/rivaflow/api/middleware/security_headers.py` (line 64-70)
- The header sets `microphone=()` (disabled), but the app has a voice transcription feature (`transcribe.py`). If the API ever serves the frontend directly, this would block microphone access.
- Currently not an issue since the frontend is served from a separate static site.
- **Fix:** If the co-located frontend mode (React build served from FastAPI) is ever used in production, update the Permissions-Policy to allow microphone access.

---

## Summary

| Severity | Count | Key Themes |
|----------|-------|------------|
| Critical | 4 | PG version mismatch, open database, unmaintained JWT library, migration chaos |
| High | 7 | Deploy not gated on tests, single worker, dependency drift, deprecated APIs |
| Medium | 10 | No structured logging, manual backups, pool sizing, CI gaps |
| Low | 10 | Cosmetic issues, minor optimizations, version string drift |

### Top 5 Actions (by impact/effort ratio)

1. **Set `autoDeploy: false` and gate deploys on CI** (H1) -- prevents broken deploys
2. **Restrict database `ipAllowList`** (C2) -- immediate security win
3. **Align CI PostgreSQL version to 18** (C1) -- one-line change
4. **Remove duplicate migration calls** (C4) -- reduces startup risk
5. **Pin TruffleHog to a release tag** (M10) -- prevents surprise CI breakage
