# Performance Testing Guide

## Overview

RivaFlow includes comprehensive performance and load tests to ensure the application scales well with large datasets and handles concurrent load effectively.

## Test Suites

### 1. Database Performance Tests

**Location:** `tests/performance/test_database_performance.py`

Tests database performance with large datasets (10,000+ sessions):

#### Test Scenarios

**Large Dataset Creation**
- Creates 10,000 test sessions spanning 2 years
- Measures bulk insert performance
- Target: < 30 seconds for 10,000 inserts

**List All Sessions**
- Queries all 10,000 sessions
- Tests full table scan performance
- Target: < 2 seconds

**Date Range Queries**
- Queries 30-day window from 10,000 sessions
- Tests index effectiveness on date columns
- Target: < 0.5 seconds

**Aggregation Queries**
- Calculates total hours, sessions, submissions
- Tests GROUP BY and SUM performance
- Target: < 0.3 seconds for 4 aggregations

**Analytics Service**
- Runs full analytics overview
- Includes multiple complex queries
- Target: < 3 seconds

**Pagination**
- Tests paginated queries (20 items per page)
- Measures average page load time
- Target: < 0.1 seconds per page

**Index Effectiveness**
- Verifies database indexes are being used
- Checks EXPLAIN QUERY PLAN output
- Ensures user_id has proper index

#### Running Database Performance Tests

```bash
# Run all database performance tests
pytest tests/performance/test_database_performance.py -v -s

# Run specific test
pytest tests/performance/test_database_performance.py::TestDatabasePerformance::test_list_sessions_performance -v -s

# Generate detailed timing report
pytest tests/performance/test_database_performance.py -v -s --durations=10
```

#### Sample Output

```
Creating 10,000 sessions...
Created 10,000 sessions in 12.34s

test_list_sessions_performance:
  List all 10,000 sessions: 1.234s
  PASSED

test_date_range_query_performance:
  Date range query (30 days): 0.156s
  PASSED

test_aggregation_query_performance:
  Aggregation queries (4 stats): 0.089s
  Total sessions: 10000
  Total hours: 10000.0
  PASSED

test_analytics_service_performance:
  Analytics overview: 2.456s
  PASSED

test_pagination_performance:
  Pagination (5 pages of 20): avg 0.045s per page
  PASSED

test_index_effectiveness:
  Query plan for user_id filter:
    SEARCH TABLE sessions USING INDEX idx_sessions_user_id (user_id=?)
  PASSED
```

### 2. API Load Tests

**Location:** `tests/performance/test_api_load.py`

Tests API performance under concurrent load:

#### Test Scenarios

**Concurrent Session Creation**
- Creates 100 sessions concurrently (20 workers)
- Tests write contention and locking
- Measures throughput (requests/second)
- Target: > 10 req/s, < 10 seconds total

**Concurrent Read Operations**
- Executes 100 concurrent read requests
- Tests read scalability
- Measures read throughput
- Target: > 20 req/s, < 5 seconds total

**Mixed Workload**
- 60% reads, 30% writes, 10% updates
- Simulates realistic user behavior
- Tests under mixed load
- Target: 95% success rate, < 15 seconds

**Analytics Endpoint Performance**
- Tests analytics with 1,000 sessions
- Measures complex query performance
- Target: < 2 seconds

**Report Generation Performance**
- Tests monthly report with 500 sessions
- Measures aggregation performance
- Target: < 1 second

#### Running API Load Tests

```bash
# Run all API load tests
pytest tests/performance/test_api_load.py -v -s

# Run concurrent tests only
pytest tests/performance/test_api_load.py::TestAPILoadPerformance -v -s

# Run endpoint-specific tests
pytest tests/performance/test_api_load.py::TestAPIEndpointPerformance -v -s
```

#### Sample Output

```
test_concurrent_session_creation:
  Creating 100 sessions concurrently...
  Time: 8.45s
  Successful: 100/100
  Failed: 0
  Throughput: 11.8 req/s
  PASSED

test_concurrent_read_operations:
  100 concurrent read requests...
  Time: 3.21s
  Successful: 100/100
  Throughput: 31.2 req/s
  PASSED

test_mixed_workload_concurrent:
  100 mixed operations (60% read, 30% write, 10% update)...
  Time: 12.67s
  Successful: 100/100
    Reads: 60
    Writes: 30
    Updates: 10
  Throughput: 7.9 req/s
  PASSED
```

### 3. Query Optimization Tests

**Location:** Included in `test_database_performance.py`

Tests for common performance anti-patterns:

#### Test Scenarios

**N+1 Query Detection**
- Verifies partner extraction doesn't cause N+1 queries
- Ensures related data is loaded efficiently
- Target: < 0.5 seconds for 100 sessions with partners

**Memory Usage**
- Measures memory footprint with 5,000 sessions
- Verifies results aren't loaded entirely into memory
- Target: < 200MB increase

## Performance Benchmarks

### Database Query Performance

| Operation | Dataset Size | Target | Typical |
|-----------|--------------|--------|---------|
| List all sessions | 10,000 | < 2s | ~1.2s |
| Date range (30d) | 10,000 | < 0.5s | ~0.15s |
| Aggregations (4 queries) | 10,000 | < 0.3s | ~0.09s |
| Analytics overview | 10,000 | < 3s | ~2.5s |
| Pagination (20 items) | 10,000 | < 0.1s | ~0.04s |

### API Load Performance

| Test | Concurrent Requests | Target | Typical |
|------|---------------------|--------|---------|
| Session creation | 100 (20 workers) | > 10 req/s | ~12 req/s |
| Read operations | 100 (20 workers) | > 20 req/s | ~31 req/s |
| Mixed workload | 100 (20 workers) | 95% success | 100% success |
| Analytics | 1,000 sessions | < 2s | ~1.8s |
| Report generation | 500 sessions | < 1s | ~0.7s |

## Optimization Recommendations

### Database Indexes

Ensure these indexes exist for optimal performance:

```sql
-- User session queries
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_user_date ON sessions(user_id, session_date DESC);

-- Date range queries
CREATE INDEX IF NOT EXISTS idx_sessions_date ON sessions(session_date DESC);

-- Class type filtering
CREATE INDEX IF NOT EXISTS idx_sessions_type ON sessions(class_type);

-- Composite index for common queries
CREATE INDEX IF NOT EXISTS idx_sessions_user_type_date ON sessions(user_id, class_type, session_date DESC);
```

### Query Optimization

1. **Use pagination** for large result sets
   ```python
   # Good
   sessions = repo.list_by_user(user_id, limit=20, offset=0)

   # Avoid
   sessions = repo.list_by_user(user_id)  # Returns all sessions
   ```

2. **Filter by date range** when possible
   ```python
   # Good
   sessions = repo.list_by_user(
       user_id,
       start_date=date.today() - timedelta(days=30),
       end_date=date.today()
   )

   # Avoid loading all sessions then filtering in Python
   ```

3. **Use aggregations in SQL** rather than Python
   ```python
   # Good
   cursor.execute("SELECT SUM(duration_mins) FROM sessions WHERE user_id = ?")

   # Avoid
   sessions = repo.list_by_user(user_id)
   total = sum(s["duration_mins"] for s in sessions)
   ```

4. **Batch related queries** to avoid N+1 problems
   ```python
   # Good - single query with JOIN or IN clause
   cursor.execute("""
       SELECT * FROM session_rolls
       WHERE session_id IN (SELECT id FROM sessions WHERE user_id = ?)
   """)

   # Avoid - separate query per session
   for session in sessions:
       rolls = get_rolls(session["id"])  # N+1 problem
   ```

### Caching Strategies

For frequently accessed, slowly changing data:

1. **User Profile** - Cache for 5 minutes
2. **Analytics Summaries** - Cache for 1 hour
3. **Milestone Progress** - Cache for 10 minutes
4. **Streaks** - Cache for 5 minutes

## Continuous Performance Monitoring

### Automated Performance Tests

Run performance tests in CI/CD pipeline:

```yaml
# .github/workflows/performance.yml
name: Performance Tests
on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly
  workflow_dispatch:

jobs:
  performance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run performance tests
        run: |
          pytest tests/performance/ -v -s --durations=10
```

### Performance Regression Detection

Compare results over time:

```bash
# Save baseline
pytest tests/performance/ --benchmark-save=baseline

# Compare current vs baseline
pytest tests/performance/ --benchmark-compare=baseline
```

### Profiling Slow Queries

Use `EXPLAIN QUERY PLAN` to debug slow queries:

```python
with get_connection() as conn:
    cursor = conn.cursor()

    # Enable profiling
    cursor.execute("EXPLAIN QUERY PLAN SELECT * FROM sessions WHERE user_id = ?", (user_id,))
    plan = cursor.fetchall()

    for row in plan:
        print(row)
    # Should show: SEARCH TABLE sessions USING INDEX idx_sessions_user_id
```

### Memory Profiling

Use `memory_profiler` for detailed memory analysis:

```python
from memory_profiler import profile

@profile
def load_large_dataset():
    sessions = repo.list_by_user(user_id)
    # Shows line-by-line memory usage
```

## Performance Troubleshooting

### Slow Queries

**Symptom:** Queries taking > 1 second

**Diagnosis:**
1. Check if indexes exist: `PRAGMA index_list('sessions')`
2. Verify index is used: `EXPLAIN QUERY PLAN ...`
3. Check dataset size: `SELECT COUNT(*) FROM sessions`

**Solutions:**
- Add missing indexes
- Use pagination
- Filter by date range
- Cache results

### High Memory Usage

**Symptom:** Memory usage growing unbounded

**Diagnosis:**
1. Check if loading all results at once
2. Verify pagination is used
3. Profile memory with `memory_profiler`

**Solutions:**
- Use pagination/streaming
- Clear unused objects
- Use generator expressions instead of lists

### Low Throughput

**Symptom:** < 10 requests/second under load

**Diagnosis:**
1. Check for database locking
2. Verify connection pooling
3. Profile slow operations

**Solutions:**
- Use connection pooling
- Optimize slow queries
- Consider read replicas for heavy read workloads
- Add caching layer

## Advanced Load Testing

### Using Locust (Optional)

For HTTP API load testing, create `locustfile.py`:

```python
from locust import HttpUser, task, between

class RivaFlowUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        # Login
        response = self.client.post("/api/auth/login", json={
            "email": "test@example.com",
            "password": "password123"
        })
        self.token = response.json()["access_token"]

    @task(3)
    def list_sessions(self):
        self.client.get(
            "/api/sessions",
            headers={"Authorization": f"Bearer {self.token}"}
        )

    @task(1)
    def create_session(self):
        self.client.post(
            "/api/sessions",
            headers={"Authorization": f"Bearer {self.token}"},
            json={
                "session_date": "2026-02-02",
                "class_type": "gi",
                "gym_name": "Test Academy",
                "duration_mins": 60,
                "intensity": 4,
                "rolls": 5
            }
        )
```

Run Locust:
```bash
# Install locust
pip install locust

# Run load test
locust -f locustfile.py --host=http://localhost:8000 --users=100 --spawn-rate=10
```

## Performance Testing Checklist

Before releasing:

- [ ] Run all performance tests: `pytest tests/performance/ -v -s`
- [ ] Verify all tests pass with acceptable metrics
- [ ] Check for N+1 query problems
- [ ] Verify indexes exist on all foreign keys
- [ ] Test with 10,000+ session dataset
- [ ] Test with 100+ concurrent requests
- [ ] Profile memory usage under load
- [ ] Document any performance regressions
- [ ] Update performance benchmarks if needed

## Related Documentation

- [Testing Guide](./TESTING.md)
- [Database Schema](../db/schema.sql)
- [API Documentation](./API.md)

---

**Last Updated:** 2026-02-02
**Related:** Task #23 from BETA_READINESS_REPORT.md
