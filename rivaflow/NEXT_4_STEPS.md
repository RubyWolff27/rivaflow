# Next 4 Steps - Post-Deployment Tasks

**Status:** Both backend and frontend are live! 🎉
**Date:** February 6, 2026
**Time to Complete:** ~2-3 hours

---

## STEP 1: Apply Logo Optimization to rivaflow-web

**Goal:** Reduce logo from 6.96MB to 223.5KB (96.6% reduction)

### 1.1 Install Pillow (if not installed)

```bash
pip install Pillow
```

### 1.2 Navigate to rivaflow-web

```bash
cd /path/to/rivaflow-web
```

### 1.3 Run optimization script

```bash
python3 /Users/rubertwolff/scratch/rivaflow/optimize_logo.py
```

**Expected output:**
```
📁 Original logo size: 6.63 MB
📂 Loading original logo...
📐 Original dimensions: 2816x1536px
💾 Backing up original to public/logo-original.png...
🔄 Resizing to 500x272px...
💾 Saving optimized PNG...
💾 Saving WebP version...

✅ Logo optimization complete!
============================================================
Original:     6.63 MB (2816x1536px)
Optimized PNG: 223.50 KB (500x272px)
WebP:         24.80 KB (500x272px)
============================================================
PNG Reduction:  96.6%
WebP Reduction: 99.6%
```

### 1.4 Commit and deploy

```bash
git add public/logo.png public/logo.webp public/logo-original.png
git commit -m "perf(frontend): Optimize logo from 6.6MB to 24.8KB (99.6% reduction)

- Original: 6.6MB (2816x1536px) - 30+ sec load on mobile
- Resized: 500x272px (web-appropriate dimensions)
- PNG: 223.5KB (96.6% reduction)
- WebP: 24.8KB (99.6% reduction, for modern browsers)

Impact:
- Reduces initial page load by 6.6MB
- Improves mobile experience dramatically
- WebP supported in 96% of browsers

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"

git push
```

### 1.5 Verify deployment

Wait ~2-3 minutes for Render to deploy, then:

```bash
curl -sI https://rivaflow.app/logo.png | grep content-length
# Should show: content-length: 228864 (223KB) instead of 6963778 (6.96MB)
```

**Status:** ⏳ Pending
**Time:** 10 minutes

---

## STEP 2: Monitor GitHub Actions Workflows

**Goal:** Verify GitHub Actions workflows are detected and running

### 2.1 Check workflow status

```bash
cd /Users/rubertwolff/scratch/rivaflow
gh workflow list
```

**Expected output:**
```
Deploy to Production  active  12345
Security Scanning     active  12346
Tests                 active  12347
```

### 2.2 If no workflows listed (wait 5-10 more minutes)

GitHub may need time to detect new workflows after first push.

### 2.3 Manually trigger a workflow

```bash
# Trigger test workflow
gh workflow run test.yml

# Check status
gh run list --limit 5
```

### 2.4 View workflow run details

```bash
# Get latest run
gh run view

# Watch live (if running)
gh run watch
```

### 2.5 Troubleshooting if workflows don't appear

**Check workflow files are on main branch:**
```bash
git ls-tree -r HEAD --name-only | grep workflows
```

Should show:
```
.github/workflows/deploy.yml
.github/workflows/security.yml
.github/workflows/test.yml
```

**Force workflow detection:**
1. Make a small change to any workflow file
2. Commit and push
3. GitHub should detect the change

**Verify GitHub Actions is enabled:**
- Go to https://github.com/RubyWolff27/rivaflow/settings/actions
- Ensure "Allow all actions and reusable workflows" is selected

### 2.6 Expected first run results

**test.yml:**
- ⚠️ Will likely FAIL (46% test pass rate)
- This is expected - we'll fix in Step 3

**security.yml:**
- ⚠️ Will show 34 Python CVEs
- This is expected - plan to fix in WAVE 2

**deploy.yml:**
- ✅ Should pass (health checks will succeed)

**Status:** ⏳ Pending
**Time:** 15 minutes + waiting time

---

## STEP 3: Complete Test Fixes (TEST_FAILURE_FIX_PLAN.md)

**Goal:** Improve test pass rate from 46% to 90%+

### Current Test Status
- Total: 199 tests
- Passing: 92 (46%)
- Failing: 57 (29%)
- Errors: 50 (25%)

### 3.1 Phase 1: PostgreSQL Test Database Setup (2 hours, 80% impact)

**Install PostgreSQL 16:**
```bash
# macOS
brew install postgresql@16
brew services start postgresql@16

# Verify installation
psql --version
# Should show: psql (PostgreSQL) 16.x
```

**Create test database:**
```bash
# Create database
createdb rivaflow_test

# Create test user (optional but recommended)
createuser rivaflow_test --createdb --pwprompt
# Enter password: test_password

# Grant privileges
psql -c "GRANT ALL PRIVILEGES ON DATABASE rivaflow_test TO rivaflow_test;"
```

**Run migrations on test database:**
```bash
cd /Users/rubertwolff/scratch/rivaflow

# Set environment
export DATABASE_URL="postgresql://rivaflow_test:test_password@localhost:5432/rivaflow_test"
export ENV=test

# Run migrations
python -m rivaflow.db.migrate

# Verify tables created
psql rivaflow_test -c "\dt"
```

**Update pytest configuration:**

Create/update `pytest.ini`:
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
env =
    DATABASE_URL=postgresql://rivaflow_test:test_password@localhost:5432/rivaflow_test
    ENV=test
    SECRET_KEY=test-secret-key-min-32-characters-long-for-testing
    DISABLE_RATE_LIMITS=true
addopts = -v --tb=short
```

**Update conftest.py:**

Edit `tests/conftest.py` and add at the top:
```python
import os
import pytest

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Configure test environment before any tests run."""
    os.environ["DATABASE_URL"] = "postgresql://rivaflow_test:test_password@localhost:5432/rivaflow_test"
    os.environ["ENV"] = "test"
    os.environ["SECRET_KEY"] = "test-secret-key-min-32-characters-long-for-testing"
    os.environ["DISABLE_RATE_LIMITS"] = "true"
    yield
    # Cleanup after all tests (optional)

@pytest.fixture(scope="function", autouse=True)
def reset_database():
    """Reset database state between tests."""
    from rivaflow.db.database import get_connection

    # Clean up test data between tests
    with get_connection() as conn:
        cursor = conn.cursor()
        # Delete test data (preserve schema)
        cursor.execute("DELETE FROM session_movements WHERE 1=1;")
        cursor.execute("DELETE FROM sessions WHERE user_id > 1;")  # Preserve admin
        cursor.execute("DELETE FROM users WHERE id > 1;")  # Preserve admin
        conn.commit()

    yield
```

**Run tests:**
```bash
pytest tests/ -v

# Expected: 160+ tests passing (80%+)
```

### 3.2 Phase 3: Fix Exception Assertions (1 hour, 5% impact)

**Find all ValueError assertions:**
```bash
grep -r "pytest.raises(ValueError)" tests/ --include="*.py"
```

**Fix pattern:**
```python
# Before
with pytest.raises(ValueError, match="email"):
    auth_service.register(...)

# After
from rivaflow.core.exceptions import ValidationError

with pytest.raises(ValidationError) as exc_info:
    auth_service.register(...)
assert "email" in str(exc_info.value)
```

**Files to update:**
- `tests/unit/test_security.py`
- `tests/unit/test_error_handling.py`
- `tests/integration/test_auth_flow.py`

### 3.3 Phase 4: Schema-Specific Fixes (2 hours)

**Common issues:**

1. **Timestamp handling:**
```python
# Fix: Use datetime objects, not strings
from datetime import datetime
session_date = datetime.now().date()  # Not string
```

2. **JSON array handling:**
```python
# Fix: Handle both SQLite (string) and PostgreSQL (native array)
import json
if isinstance(techniques, str):
    techniques = json.loads(techniques)
```

3. **Foreign key constraints:**
```python
# Fix: Ensure test data satisfies constraints
# Create user first, then session
user = create_test_user()
session = create_test_session(user_id=user.id)
```

### 3.4 Commit test fixes

```bash
git add tests/ pytest.ini
git commit -m "test: Fix test suite for PostgreSQL compatibility

Improves test pass rate from 46% to 90%+:

Phase 1: PostgreSQL test database configuration
- Configure pytest to use PostgreSQL instead of SQLite
- Add test environment setup fixtures
- Reset database state between tests

Phase 3: Fix exception type assertions
- Replace ValueError with ValidationError
- Update assertion patterns

Phase 4: Schema-specific fixes
- Fix timestamp handling
- Fix JSON array handling
- Ensure foreign key constraints satisfied

Result: 180+/199 tests passing (90%+ pass rate)

Implements TEST_FAILURE_FIX_PLAN.md phases 1, 3, 4.
Phase 2 (rate limiting) already complete.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"

git push
```

**Validation:**
```bash
pytest tests/ -v --tb=short | tail -10
# Should show: ===== X passed, Y failed in Z.XXs =====
# Target: 180+ passed
```

**Status:** ⏳ Pending
**Time:** 5 hours (mostly Phase 1 PostgreSQL setup)

---

## STEP 4: Set up Sentry Monitoring (MONITORING_SETUP.md)

**Goal:** Production error tracking and monitoring

### 4.1 Create Sentry Account

1. Go to https://sentry.io
2. Sign up for free tier (5,000 errors/month)
3. Create organization: "RivaFlow"

### 4.2 Create Backend Project

1. Click "Create Project"
2. Platform: Python
3. Name: "rivaflow-api"
4. Copy DSN (looks like: `https://abc123@o123456.ingest.sentry.io/7654321`)

### 4.3 Create Frontend Project

1. Click "Create Project"
2. Platform: React
3. Name: "rivaflow-web"
4. Copy DSN

### 4.4 Install Sentry SDK (Backend)

```bash
cd /Users/rubertwolff/scratch/rivaflow

# Install
pip install "sentry-sdk[fastapi]==1.40.0"

# Add to requirements.txt
echo 'sentry-sdk[fastapi]==1.40.0' >> requirements.txt
```

### 4.5 Configure Sentry in Backend

Edit `rivaflow/api/main.py` and add after imports (around line 27):

```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

# Initialize Sentry (only in production)
if not settings.IS_TEST and os.getenv("SENTRY_DSN"):
    sentry_sdk.init(
        dsn=os.getenv("SENTRY_DSN"),
        environment=os.getenv("ENV", "production"),
        release=f"rivaflow@{os.getenv('VERSION', '0.2.0')}",
        traces_sample_rate=0.1,  # 10% performance monitoring
        profiles_sample_rate=0.1,  # 10% profiling
        integrations=[
            FastApiIntegration(),
            StarletteIntegration(),
        ],
    )
    logging.info("Sentry error tracking enabled")
```

### 4.6 Add Sentry DSN to Render

1. Go to Render Dashboard → rivaflow-api → Environment
2. Add environment variable:
   - Key: `SENTRY_DSN`
   - Value: `<your-backend-sentry-dsn>`
3. Click "Save Changes"
4. Render will auto-redeploy

### 4.7 Install Sentry SDK (Frontend)

```bash
cd /path/to/rivaflow-web

npm install @sentry/react --save
```

### 4.8 Configure Sentry in Frontend

Edit `web/src/main.tsx` or `web/src/App.tsx` (add at top):

```typescript
import * as Sentry from "@sentry/react";

// Initialize Sentry
if (import.meta.env.PROD && import.meta.env.VITE_SENTRY_DSN) {
  Sentry.init({
    dsn: import.meta.env.VITE_SENTRY_DSN,
    environment: import.meta.env.MODE,
    release: "rivaflow-web@0.2.0",
    integrations: [
      Sentry.browserTracingIntegration(),
      Sentry.replayIntegration(),
    ],
    tracesSampleRate: 0.1,
    replaysSessionSampleRate: 0.1,
    replaysOnErrorSampleRate: 1.0,
  });
}
```

### 4.9 Add Sentry to ErrorBoundary

Edit `src/components/ErrorBoundary.tsx` in `componentDidCatch`:

```typescript
componentDidCatch(error: Error, errorInfo: ErrorInfo) {
  console.error('ErrorBoundary caught:', error, errorInfo);

  // Send to Sentry in production
  if (import.meta.env.PROD) {
    Sentry.captureException(error, { extra: errorInfo });
  }

  this.setState({ error, errorInfo });
}
```

### 4.10 Add Sentry DSN to Render (Frontend)

1. Render Dashboard → rivaflow-web → Environment
2. Add: `VITE_SENTRY_DSN=<your-frontend-sentry-dsn>`
3. Save and redeploy

### 4.11 Test Sentry Integration

**Backend test:**
```bash
# Add temporary test endpoint to main.py
@app.get("/sentry-test")
def test_sentry():
    1 / 0  # Intentional error
    return {"status": "ok"}

# Deploy and visit:
curl https://api.rivaflow.app/sentry-test
```

Check Sentry dashboard for error.

**Frontend test:**
```typescript
// Add button in Dashboard.tsx temporarily
<button onClick={() => { throw new Error("Sentry test"); }}>
  Test Error
</button>
```

### 4.12 Set up UptimeRobot (Bonus)

1. Go to https://uptimerobot.com
2. Sign up (free: 50 monitors)
3. Add monitor:
   - Type: HTTP(s)
   - URL: `https://api.rivaflow.app/health`
   - Name: "RivaFlow API"
   - Interval: 5 minutes
4. Add alert: Your email

### 4.13 Commit Sentry integration

```bash
git add rivaflow/api/main.py requirements.txt
git commit -m "feat(monitoring): Add Sentry error tracking

Implements production error monitoring:
- Sentry SDK for FastAPI backend
- 10% performance sampling
- Environment-based configuration
- Only active in production (not tests)

Next: Add frontend Sentry integration

Part of MONITORING_SETUP.md implementation.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"

git push
```

**Status:** ⏳ Pending
**Time:** 1.5 hours

---

## Progress Tracking

### Step 1: Logo Optimization
- [ ] Install Pillow
- [ ] Run optimization script
- [ ] Commit and push
- [ ] Verify deployment (logo < 250KB)

### Step 2: GitHub Actions
- [ ] Check workflow list
- [ ] Manually trigger test workflow
- [ ] Review first run results
- [ ] Fix any workflow issues

### Step 3: Test Fixes
- [ ] Install PostgreSQL 16
- [ ] Create rivaflow_test database
- [ ] Run migrations on test DB
- [ ] Update pytest.ini
- [ ] Update conftest.py
- [ ] Fix exception assertions
- [ ] Fix schema-specific issues
- [ ] Verify 90%+ pass rate
- [ ] Commit and push

### Step 4: Sentry Monitoring
- [ ] Create Sentry account
- [ ] Create backend project (get DSN)
- [ ] Create frontend project (get DSN)
- [ ] Install Sentry SDK (backend)
- [ ] Configure backend integration
- [ ] Add SENTRY_DSN to Render (backend)
- [ ] Install Sentry SDK (frontend)
- [ ] Configure frontend integration
- [ ] Add to ErrorBoundary
- [ ] Add VITE_SENTRY_DSN to Render (frontend)
- [ ] Test backend integration
- [ ] Test frontend integration
- [ ] Set up UptimeRobot (bonus)

---

## Estimated Timeline

**Today (Feb 6):**
- Step 1: Logo optimization (10 min)
- Step 2: GitHub Actions monitoring (15 min + waiting)

**Tomorrow (Feb 7):**
- Step 3: PostgreSQL setup (2 hours)
- Step 3: Test fixes (3 hours)

**Feb 8:**
- Step 4: Sentry setup (1.5 hours)

**Total:** ~7 hours hands-on work

---

## Success Criteria

After completing all 4 steps:

✅ Logo loads in <1 second on mobile (currently 30+ seconds)
✅ CI/CD pipeline running on every commit
✅ 90%+ test pass rate (currently 46%)
✅ Real-time error tracking in production
✅ Uptime monitoring with alerts
✅ Production-ready monitoring stack

---

**Next:** Start with Step 1 (Logo Optimization)
**Status:** Ready to begin
**Date:** February 6, 2026
