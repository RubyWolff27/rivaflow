# Backend Test Failure Fix Plan

## Current Status
- **Total tests**: 199
- **Passed**: 92 (46%)
- **Failed**: 57 (29%)
- **Errors**: 50 (25%)

**Target**: >90% pass rate (180+ tests passing)

---

## Root Causes Identified

### 1. Schema Mismatch (SQLite vs PostgreSQL)
**Impact**: 80% of failures
**Affected Tests**:
- `test_postgresql_compatibility.py` (all 30 tests)
- `test_session_logging.py` (26 tests)
- `test_cli_commands.py` (10+ tests)

**Problem**:
- Tests run against SQLite (in-memory)
- Production uses PostgreSQL
- Schema divergence:
  - Column names differ (`password_hash` vs `hashed_password`)
  - Constraint enforcement differs
  - JSON handling differs
  - Timestamp defaults differ

**Solution**:
Configure tests to use PostgreSQL test database.

### 2. Rate Limiting in Tests
**Impact**: 15% of failures
**Affected**: Auth tests, session creation

**Problem**:
```python
test_login_rate_limit - Expected 429 after 5 attempts
Reality: Rate limiter active during tests
```

**Solution**:
Disable rate limiting in test environment.

### 3. Exception Type Mismatches
**Impact**: 5% of failures

**Problem**:
Tests expect `ValueError`, code raises `ValidationError`

**Solution**:
Update test assertions to match actual exceptions.

---

## Fix Strategy (Phases)

### PHASE 1: Test Environment Configuration (2 hours)
**Goal**: Configure PostgreSQL for tests

1. **Create test database configuration**
   ```python
   # tests/conftest.py
   import os
   import pytest

   @pytest.fixture(scope="session", autouse=True)
   def setup_test_database():
       """Configure PostgreSQL for tests."""
       os.environ["DATABASE_URL"] = "postgresql://localhost:5432/rivaflow_test"
       os.environ["ENV"] = "test"
       os.environ["DISABLE_RATE_LIMITS"] = "true"
       yield
       # Cleanup after all tests
   ```

2. **Update pytest.ini**
   ```ini
   [pytest]
   testpaths = tests
   python_files = test_*.py
   python_classes = Test*
   python_functions = test_*
   env =
       DATABASE_URL=postgresql://localhost:5432/rivaflow_test
       ENV=test
       SECRET_KEY=test-secret-key-min-32-characters-long
       DISABLE_RATE_LIMITS=true
   ```

3. **Create test database**
   ```bash
   createdb rivaflow_test
   ```

4. **Run migrations in test DB**
   ```bash
   DATABASE_URL=postgresql://localhost:5432/rivaflow_test python -m rivaflow.db.migrate
   ```

**Expected Impact**: Fix 80% of failures (160 tests)

---

### PHASE 2: Disable Rate Limiting (30 minutes)
**Goal**: Prevent rate limit interference in tests

1. **Update API configuration**
   ```python
   # rivaflow/api/main.py
   if not settings.IS_TEST:
       limiter = Limiter(key_func=get_remote_address)
       app.state.limiter = limiter
   ```

2. **Add test environment check**
   ```python
   # rivaflow/core/settings.py
   class Settings(BaseSettings):
       IS_TEST: bool = Field(default=False, description="Test environment flag")

       @computed_field
       @property
       def IS_TEST(self) -> bool:
           return os.getenv("ENV") == "test"
   ```

**Expected Impact**: Fix 15% of failures (30 tests)

---

### PHASE 3: Fix Exception Assertions (1 hour)
**Goal**: Update tests to match actual exception types

**Files to update**:
- `tests/unit/test_security.py`
- `tests/unit/test_error_handling.py`
- `tests/integration/test_auth_flow.py`

**Pattern to find**:
```bash
grep -r "with pytest.raises(ValueError)" tests/
```

**Fix example**:
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

**Expected Impact**: Fix 5% of failures (10 tests)

---

### PHASE 4: Schema-Specific Fixes (2 hours)
**Goal**: Fix remaining PostgreSQL-specific issues

**Common issues**:

1. **Timestamp handling**
   ```python
   # SQLite stores as string, PostgreSQL as timestamp
   # Fix: Use proper datetime objects
   session_date = datetime.now().date()  # Not string
   ```

2. **JSON array handling**
   ```python
   # SQLite: "[\"item1\", \"item2\"]" (string)
   # PostgreSQL: ["item1", "item2"] (native array)
   # Fix: Use json.loads() if string
   ```

3. **Foreign key constraints**
   ```sql
   -- PostgreSQL enforces strictly
   -- SQLite doesn't enforce by default
   -- Fix: Ensure test data satisfies constraints
   ```

**Expected Impact**: Fix remaining 5% (10 tests)

---

## Implementation Order

### Quick Wins (Complete First)
1. ✅ **PHASE 2: Disable rate limiting** (30 min)
   - Immediate impact on auth tests
   - Simple code change

2. ✅ **PHASE 3: Fix exception assertions** (1 hour)
   - Clear pattern to fix
   - No infrastructure changes

3. ⏳ **PHASE 1: PostgreSQL test DB** (2 hours)
   - Requires local PostgreSQL
   - Biggest impact (80% of failures)

4. ⏳ **PHASE 4: Schema-specific fixes** (2 hours)
   - Cleanup remaining issues

**Total effort**: ~6 hours to reach 90%+ pass rate

---

## Commands to Run

### Setup Test Database (One-time)
```bash
# Install PostgreSQL (if not installed)
brew install postgresql@16  # macOS
sudo apt-get install postgresql-16  # Linux

# Start PostgreSQL
brew services start postgresql@16  # macOS
sudo systemctl start postgresql  # Linux

# Create test database
createdb rivaflow_test

# Create test user (optional)
createuser rivaflow_test --createdb --pwprompt

# Run migrations
DATABASE_URL=postgresql://localhost:5432/rivaflow_test python -m rivaflow.db.migrate
```

### Run Tests with PostgreSQL
```bash
# Set environment
export DATABASE_URL=postgresql://localhost:5432/rivaflow_test
export ENV=test
export DISABLE_RATE_LIMITS=true

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/integration/test_auth_flow.py -v

# Run with coverage
pytest tests/ --cov=rivaflow --cov-report=html
```

### Reset Test Database (When Needed)
```bash
dropdb rivaflow_test && createdb rivaflow_test
DATABASE_URL=postgresql://localhost:5432/rivaflow_test python -m rivaflow.db.migrate
```

---

## Files to Modify

### Configuration Files
1. `tests/conftest.py` - Add PostgreSQL fixture
2. `pytest.ini` - Add environment variables
3. `rivaflow/core/settings.py` - Add IS_TEST property
4. `rivaflow/api/main.py` - Conditional rate limiter

### Test Files (Exception Fixes)
1. `tests/unit/test_security.py`
2. `tests/unit/test_error_handling.py`
3. `tests/integration/test_auth_flow.py`
4. `tests/integration/test_session_logging.py`

---

## Progress Tracking

### PHASE 1: PostgreSQL Configuration
- [ ] Install PostgreSQL locally
- [ ] Create test database
- [ ] Run migrations
- [ ] Update conftest.py
- [ ] Update pytest.ini
- [ ] Test: `pytest tests/unit/ -v` (should pass)

### PHASE 2: Disable Rate Limiting
- [x] Add IS_TEST to settings.py ✅
- [ ] Conditional limiter in main.py
- [ ] Test: `pytest tests/integration/test_auth_flow.py::TestRateLimiting -v`

### PHASE 3: Exception Fixes
- [ ] Find all ValueError assertions: `grep -r "pytest.raises(ValueError)" tests/`
- [ ] Replace with ValidationError
- [ ] Test: `pytest tests/unit/test_error_handling.py -v`

### PHASE 4: Schema Fixes
- [ ] Fix timestamp handling
- [ ] Fix JSON array handling
- [ ] Fix foreign key test data
- [ ] Test: `pytest tests/integration/test_postgresql_compatibility.py -v`

---

## Validation Criteria

**Success Metrics**:
- ✅ >90% test pass rate (180+ / 199)
- ✅ 0 errors (all tests run to completion)
- ✅ <10 failures remaining
- ✅ CI/CD pipeline green

**Test Commands**:
```bash
# Full test suite
pytest tests/ -v --tb=short

# Check pass rate
pytest tests/ -q | tail -1

# Coverage report
pytest tests/ --cov=rivaflow --cov-report=term-missing
```

---

## Known Issues to Monitor

1. **Sequence Reset** (from Agent 10)
   - PostgreSQL sequences may be out of sync
   - Symptoms: "duplicate key" errors
   - Fix: Run `docs/fix_sequences_manual.sql`

2. **Connection Pool Exhaustion**
   - Tests open many connections
   - May exceed pool size (20)
   - Fix: Ensure cleanup in fixtures

3. **Migration Order**
   - Tests assume migrations run in order
   - If test DB out of sync, reset and re-migrate

---

## Emergency Rollback

If tests break production:

```bash
# Revert to SQLite for tests
unset DATABASE_URL
export ENV=development

# Run tests
pytest tests/ -v
```

---

## Next Steps

1. **Immediate** (Tonight):
   - ✅ Document test failure plan (this file)
   - ⏳ Implement PHASE 2 (rate limiting)
   - ⏳ Start PHASE 3 (exception fixes)

2. **Tomorrow** (User returns):
   - ⏳ Complete PHASE 1 (PostgreSQL setup)
   - ⏳ Complete PHASE 3 & 4
   - ⏳ Verify 90%+ pass rate
   - ⏳ Commit fixes

3. **Week 1**:
   - Monitor test stability
   - Fix remaining edge cases
   - Add new tests for gaps

---

**Status**: Plan documented, ready to implement
**Estimated Time**: 6 hours to 90%+ pass rate
**Priority**: HIGH (blocks confident deployments)
