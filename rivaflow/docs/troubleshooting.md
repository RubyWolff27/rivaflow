# RivaFlow Troubleshooting Guide

Common issues and how to solve them.

---

## Table of Contents

- [Installation Issues](#installation-issues)
- [Authentication Problems](#authentication-problems)
- [Logging & Data Issues](#logging--data-issues)
- [API Errors](#api-errors)
- [CLI Problems](#cli-problems)
- [Performance Issues](#performance-issues)
- [Database Issues](#database-issues)
- [Network & Connectivity](#network--connectivity)

---

## Installation Issues

### "Command not found: rivaflow"

**Problem:** Shell can't find rivaflow command after installation.

**Solution:**
```bash
# 1. Verify installation
pip list | grep rivaflow

# 2. Check Python PATH
python -m site --user-base

# 3. Add to PATH (add to ~/.bashrc or ~/.zshrc)
export PATH="$PATH:$(python -m site --user-base)/bin"

# 4. Reload shell
source ~/.bashrc  # or ~/.zshrc

# 5. Test
rivaflow --version
```

**Alternative:** Use Python module syntax:
```bash
python -m rivaflow --version
```

---

### "pip: command not found"

**Problem:** pip not installed.

**Solution:**
```bash
# macOS/Linux
python -m ensurepip --upgrade

# Or install Python from python.org
```

---

### "Permission denied" during install

**Problem:** Trying to install system-wide without permissions.

**Solution:**
```bash
# Install for current user only (recommended)
pip install --user rivaflow

# Or use virtual environment (best practice)
python -m venv venv
source venv/bin/activate
pip install rivaflow
```

---

### Dependencies fail to install

**Problem:** Conflicting package versions.

**Solution:**
```bash
# Use virtual environment
python -m venv rivaflow-env
source rivaflow-env/bin/activate
pip install rivaflow

# If still fails, upgrade pip
pip install --upgrade pip
pip install rivaflow
```

---

## Authentication Problems

### Can't log in - "Invalid credentials"

**Checklist:**
1. Email is case-sensitive (usually lowercase)
2. Password is exact (check caps lock)
3. Account exists (try forgot password)
4. Not using old password (if recently reset)

**Debug:**
```bash
# Test login
rivaflow auth login

# If successful, check token
rivaflow auth whoami
```

---

### "Token expired" errors

**Problem:** Access tokens expire after 30 minutes.

**Solution:**
```bash
# Get new token with refresh token
rivaflow auth refresh

# Or just login again
rivaflow auth login
```

**For API users:**
```bash
POST /api/v1/auth/refresh
{
  "refresh_token": "your_refresh_token"
}
```

---

### Password reset email not received

**Checklist:**
1. Check spam folder
2. Verify email address is correct
3. Wait 5 minutes (can be delayed)
4. Check email service is working

**Still not working?**
```bash
# Try again (rate limited to 3/hour)
rivaflow auth forgot-password
```

Contact support if issue persists.

---

### "SECRET_KEY not set" error

**Problem:** Environment variable missing (for self-hosted).

**Solution:**
```bash
# Create .env file
echo "SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(32))')" > .env

# Or export directly
export SECRET_KEY="your-secret-key-here"
```

---

## Logging & Data Issues

### Sessions not showing up

**Debug steps:**
```bash
# 1. Verify you're logged in as correct user
rivaflow auth whoami

# 2. List recent sessions
rivaflow list sessions --limit 10

# 3. Check database directly (advanced)
rivaflow debug sessions

# 4. Check date filters
rivaflow analytics week  # Should show this week's sessions
```

**Common causes:**
- Logged session for different user
- Date filter excluding session
- Session date in the future (rejected)
- Database not synced (offline mode)

---

### Duplicate sessions appearing

**Problem:** Same session logged multiple times.

**Solution:**
```bash
# Delete duplicates
rivaflow delete <session_id>

# List all sessions to find IDs
rivaflow list sessions
```

**Prevention:** Check `rivaflow list sessions` before logging to avoid duplicates.

---

### Can't edit past sessions

**Problem:** Sessions locked or not found.

**Debug:**
```bash
# Verify session exists
rivaflow get <session_id>

# Verify you own the session (user_id matches)
rivaflow auth whoami

# Try update via API
curl -X PUT /api/v1/sessions/<id> \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"notes": "Updated"}'
```

---

### Streaks not updating

**Common causes:**
1. **Check-in streak** - Need to log session, readiness, OR rest daily
2. **Session streak** - Need to log training session daily (rest breaks it)
3. **Readiness streak** - Need to log readiness daily

**Verify:**
```bash
# Check today's check-in status
rivaflow

# Log readiness to maintain check-in streak
rivaflow readiness

# View current streaks
rivaflow streak
```

---

## API Errors

### 401 Unauthorized

**Causes:**
- Missing Authorization header
- Token expired (30 min lifetime)
- Invalid token format

**Solution:**
```bash
# Verify token format
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...

# Get new token
POST /api/v1/auth/refresh
{
  "refresh_token": "your_refresh_token"
}

# Or login again
POST /api/v1/auth/login
```

---

### 429 Too Many Requests

**Problem:** Rate limit exceeded.

**Limits:**
- Auth endpoints: 5 requests/minute
- Password reset: 3 requests/hour
- General API: 100 requests/minute

**Solution:**
Wait for rate limit window to reset. Check headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1643723400  # Unix timestamp
```

---

### 422 Validation Error

**Problem:** Invalid request data.

**Check:**
- Required fields present
- Data types correct (int, string, date)
- Values in valid ranges (intensity 1-5)
- Dates not in future

**Example error:**
```json
{
  "detail": [
    {
      "loc": ["body", "intensity"],
      "msg": "value must be between 1 and 5",
      "type": "value_error"
    }
  ]
}
```

---

### 500 Internal Server Error

**Problem:** Server-side error.

**Steps:**
1. Check server logs (if self-hosting)
2. Retry request (might be transient)
3. Report issue if persistent

**Report with:**
- Endpoint called
- Request payload
- Error message
- Timestamp

---

## CLI Problems

### Commands hang or freeze

**Causes:**
- Network timeout
- Database locked
- Large data export

**Solution:**
```bash
# Cancel with Ctrl+C

# Check network
ping rivaflow.onrender.com

# Check database
rivaflow debug db-status

# Try with timeout
timeout 30s rivaflow log
```

---

### Colors/formatting broken

**Problem:** Terminal doesn't support ANSI colors.

**Solution:**
```bash
# Disable colors
export NO_COLOR=1
rivaflow

# Or use plain output
rivaflow --no-color
```

---

### Unicode characters not displaying

**Problem:** Terminal encoding issue.

**Solution:**
```bash
# Set UTF-8 encoding
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8

# Add to ~/.bashrc or ~/.zshrc for persistence
```

---

### Prompts not appearing

**Problem:** Interactive input broken.

**Solution:**
```bash
# Try non-interactive mode (if available)
rivaflow log --non-interactive

# Or pipe input
echo "gi\nTest Gym\n90" | rivaflow log

# Check Python version (3.11+ required)
python --version
```

---

## Performance Issues

### Slow analytics queries

**Problem:** Large dataset making queries slow.

**Solution:**
```bash
# Use date filters
rivaflow analytics week    # Faster than 'all'

# Limit results
rivaflow list sessions --limit 50

# Optimize database (self-hosted)
rivaflow db optimize
```

---

### Slow session logging

**Problem:** Network latency or database lock.

**Debug:**
```bash
# Check network speed
time curl -I https://rivaflow.onrender.com

# Use offline mode (if available)
rivaflow log --offline

# Sync later
rivaflow sync
```

---

## Database Issues

### "Database is locked" error

**Problem:** Another process accessing database.

**Solution:**
```bash
# Find processes using database
lsof | grep rivaflow

# Kill stuck processes
pkill -f rivaflow

# Retry operation
rivaflow log
```

---

### Corrupted database

**Problem:** Database file corrupted (rare).

**Solution:**
```bash
# 1. Export data IMMEDIATELY
rivaflow export --output backup.json

# 2. Reinitialize database
rivaflow db init --force

# 3. Import data
rivaflow import backup.json

# If fails, contact support with backup.json
```

---

### Missing data after upgrade

**Problem:** Migration failed or incomplete.

**Solution:**
```bash
# Run migrations manually
rivaflow db migrate

# Check migration status
rivaflow db migrate --status

# Rollback if needed
rivaflow db migrate --rollback
```

---

## Network & Connectivity

### "Connection refused" error

**Causes:**
- API server down
- Network firewall blocking
- Wrong base URL

**Debug:**
```bash
# Test connectivity
curl https://rivaflow.onrender.com/health

# Check DNS
nslookup rivaflow.onrender.com

# Check firewall
# (varies by system)
```

---

### SSL certificate errors

**Problem:** HTTPS certificate validation failing.

**Solution:**
```bash
# Update CA certificates (Linux)
sudo update-ca-certificates

# macOS
# Install latest Python from python.org

# Temporary workaround (NOT RECOMMENDED)
export CURL_CA_BUNDLE=""
```

---

### Timeout errors

**Problem:** Slow network or server overload.

**Solution:**
```bash
# Increase timeout (if supported)
rivaflow --timeout 60 log

# Or configure in ~/.rivaflow/config
timeout: 60
```

---

## Advanced Debugging

### Enable debug logging

```bash
# Set log level
export RIVAFLOW_LOG_LEVEL=DEBUG

# Run command
rivaflow log

# Check logs
cat ~/.rivaflow/logs/rivaflow.log
```

---

### Check configuration

```bash
# Show current config
rivaflow config show

# Validate config
rivaflow config validate

# Reset to defaults
rivaflow config reset
```

---

### Database inspection

```bash
# Check database status
rivaflow db status

# Count records
rivaflow db count sessions
rivaflow db count users

# Verify integrity
rivaflow db check
```

---

## Getting Help

If none of these solutions work:

1. **Check existing issues:** [GitHub Issues](https://github.com/rivaflow/rivaflow/issues)
2. **Search discussions:** [GitHub Discussions](https://github.com/rivaflow/rivaflow/discussions)
3. **Create new issue:** Include:
   - RivaFlow version (`rivaflow --version`)
   - Python version (`python --version`)
   - Operating system
   - Full error message
   - Steps to reproduce
4. **Email support:** support@rivaflow.com

---

## Reporting Bugs

**Good bug report includes:**

```
**Environment:**
- RivaFlow version: 0.2.0
- Python version: 3.11.5
- OS: macOS 14.0
- Installation method: pip

**Expected behavior:**
Session should be logged successfully.

**Actual behavior:**
Error: "intensity must be between 1 and 5"

**Steps to reproduce:**
1. Run `rivaflow log`
2. Enter intensity: 4
3. Error appears

**Error message:**
[Full error output here]

**Additional context:**
This started happening after updating to v0.2.0.
```

---

**Still stuck?** support@rivaflow.com
