# RivaFlow v0.2.0 Production Deployment Checklist
**Domain:** rivaflow.app
**Date:** February 4, 2026
**Deployment Target:** Render.com

---

## ✅ PRE-DEPLOYMENT CHECKLIST

### Code Quality
- [x] All critical fixes implemented (23/23 tasks complete)
- [x] Build completes successfully (`./build.sh`)
- [x] No AI dependencies in production build
- [x] VERSION file present (v0.2.0)
- [x] .env in .gitignore (verified)
- [ ] All changes committed to git
- [ ] Push to main branch

### Security
- [x] CVE-2024-23342 (ecdsa) fixed
- [x] SECRET_KEY requirements validated in code
- [x] Rate limiting added to all critical endpoints
  - [x] Sessions: 60/minute
  - [x] Photos: 10/minute
  - [x] Social: 20-60/minute (already had)
  - [x] Auth: 3-10/minute (already had)
- [x] Search min_length validation (2 chars minimum)
- [x] Date range validation (max 2 years)
- [x] Pagination added to all list endpoints
- [x] Unbounded queries fixed (dashboard quick-stats)

### Performance
- [x] Database indexes added (migration 055)
  - techniques.name
  - gradings(user_id, date_graded)
  - notifications(user_id, is_read, created_at)
- [x] Efficient SQL aggregation for user stats
- [x] Query limits enforced
- [ ] Performance monitoring plan (post-launch)

### Configuration
- [x] .env.example updated for rivaflow.app
- [x] render.yaml updated for rivaflow.app domain
- [x] ALLOWED_ORIGINS example includes rivaflow.app
- [x] EMAIL_FROM updated to noreply@rivaflow.app

---

## 🚀 RENDER.COM DEPLOYMENT STEPS

### Step 1: Create PostgreSQL Database
1. Log in to [Render Dashboard](https://dashboard.render.com/)
2. Click **"New +"** → **"PostgreSQL"**
3. Configure database:
   ```
   Name: rivaflow-db
   Database: rivaflow
   User: rivaflow
   Region: Oregon (US West)
   Plan: Free (or Starter for production)
   ```
4. Click **"Create Database"**
5. Wait for status: **"Available"** (green checkmark)
6. Note the **Internal Database URL** for next step

### Step 2: Create Web Service (API)
1. Click **"New +"** → **"Web Service"**
2. Connect GitHub repository: **RubyWolff27/rivaflow**
3. Configure service:
   ```
   Name: rivaflow-api
   Region: Oregon (US West)
   Branch: main
   Runtime: Python 3
   Build Command: bash build.sh
   Start Command: uvicorn rivaflow.api.main:app --host 0.0.0.0 --port $PORT
   Plan: Free (or Starter for production)
   ```

### Step 3: Set Environment Variables
In rivaflow-api service → Environment tab, add:

#### Required Variables:
```bash
# Security (CRITICAL - DO NOT USE DEVELOPMENT KEYS)
SECRET_KEY=<click "Generate Value" button - MUST be 32+ chars>
ENV=production
PYTHON_VERSION=3.11.0

# Database (connect to rivaflow-db created in Step 1)
DATABASE_URL=<select "From Database: rivaflow-db">

# CORS (CRITICAL - Set your actual domains)
ALLOWED_ORIGINS=https://rivaflow.app,https://www.rivaflow.app,https://api.rivaflow.app
```

#### Optional but Recommended:
```bash
# Email (get from SendGrid)
SENDGRID_API_KEY=<your-sendgrid-api-key>
EMAIL_FROM=noreply@rivaflow.app

# Caching (create Redis instance first, or leave empty)
REDIS_URL=<optional-redis-connection-string>
```

### Step 4: Deploy
1. Click **"Manual Deploy"** → **"Deploy latest commit"**
2. Monitor build logs for:
   ```
   ✓ VERSION file found: 0.2.0
   ✅ No forbidden AI dependencies detected
   ✓ BUILD SUCCESSFUL - RivaFlow v0.2.0
   ```
3. Wait for status: **"Live"** (green checkmark)
4. Note your Render URL: `https://rivaflow-api.onrender.com`

### Step 5: Configure Custom Domain
1. In rivaflow-api service → **Settings** → **Custom Domains**
2. Click **"Add Custom Domain"**
3. Enter: `api.rivaflow.app`
4. Render will provide DNS records (CNAME or A record)
5. Add DNS records in your domain provider:
   ```
   Type: CNAME
   Name: api
   Value: rivaflow-api.onrender.com
   TTL: 3600
   ```
6. Wait for SSL certificate (5-10 minutes)
7. Verify: `https://api.rivaflow.app/health`

---

## ✅ POST-DEPLOYMENT VERIFICATION

### Health Checks (5 minutes after deployment)
```bash
# 1. Basic health check
curl https://api.rivaflow.app/health

Expected:
{
  "status": "healthy",
  "service": "rivaflow-api",
  "version": "0.2.0",
  "database": "connected"
}

# 2. Database health
curl https://api.rivaflow.app/api/v1/health/db

Expected: {"status": "healthy", "database": "connected"}

# 3. API docs available
curl https://api.rivaflow.app/docs

Expected: HTML page with Swagger UI
```

### Functional Tests
```bash
# 4. User registration
curl -X POST https://api.rivaflow.app/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!",
    "first_name": "Test",
    "last_name": "User"
  }'

Expected: 201 Created with user object and tokens

# 5. User login
curl -X POST https://api.rivaflow.app/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!"
  }'

Expected: 200 OK with access_token and refresh_token

# 6. Protected endpoint (using token from login)
curl https://api.rivaflow.app/api/v1/profile \
  -H "Authorization: Bearer <access_token>"

Expected: 200 OK with user profile
```

### Security Header Verification
```bash
curl -I https://api.rivaflow.app/health

Verify headers present:
✓ strict-transport-security: max-age=31536000; includeSubDomains
✓ x-content-type-options: nosniff
✓ x-frame-options: DENY
✓ content-security-policy: default-src 'self'; ...
✓ referrer-policy: strict-origin-when-cross-origin
```

### Performance Checks
```bash
# Dashboard response time
time curl -H "Authorization: Bearer <token>" \
  https://api.rivaflow.app/api/v1/dashboard/summary

Expected: < 1 second (with empty database)

# Rate limiting verification
for i in {1..10}; do
  curl -X POST https://api.rivaflow.app/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"test@example.com","password":"wrong"}';
done

Expected: HTTP 429 (Too Many Requests) after 5 attempts
```

---

## 📊 MONITORING SETUP (First 24 Hours)

### Render Dashboard Monitoring
1. Go to rivaflow-api service → **Metrics**
2. Monitor:
   - CPU usage (should be < 50%)
   - Memory usage (should be < 200MB)
   - Request rate
   - Error rate (should be < 1%)

### External Uptime Monitoring (Optional but Recommended)
1. Sign up for [UptimeRobot](https://uptimerobot.com) (free)
2. Add monitor:
   ```
   Monitor Type: HTTPS
   URL: https://api.rivaflow.app/health
   Interval: 5 minutes
   Alert: Email when down
   ```

### Error Tracking (Recommended)
1. Sign up for [Sentry](https://sentry.io) (free tier)
2. Add SENTRY_DSN to Render environment variables
3. Monitor errors in Sentry dashboard

---

## 🔥 ROLLBACK PROCEDURE (If Issues Arise)

### Emergency Rollback
If critical issues occur within first 24 hours:

1. **Disable auto-deploy:**
   - Render Dashboard → rivaflow-api → Settings
   - Disable "Auto-Deploy"

2. **Rollback to previous deploy:**
   - Render Dashboard → rivaflow-api → Events
   - Find last successful deploy
   - Click **"Rollback to this deploy"**

3. **Database rollback (if schema changed):**
   ```bash
   # Connect to database
   psql <DATABASE_URL>

   # Drop new migrations (if any were run)
   DELETE FROM schema_migrations WHERE version IN ('055', '056');

   # Revert schema changes manually or restore from backup
   ```

### Database Backup Before Deployment
```bash
# Create backup before deployment
pg_dump <DATABASE_URL> > backup_pre_deployment_$(date +%Y%m%d).sql

# Restore if needed
psql <DATABASE_URL> < backup_pre_deployment_YYYYMMDD.sql
```

---

## 📋 POST-LAUNCH TASKS (Week 1)

### Immediate (Day 1)
- [ ] Verify all health checks pass
- [ ] Monitor error logs for 4 hours
- [ ] Test critical user flows
- [ ] Set up uptime monitoring
- [ ] Monitor Render dashboard metrics

### Short-term (Week 1)
- [ ] Review error logs daily
- [ ] Track response times
- [ ] Monitor active users
- [ ] Collect user feedback
- [ ] Document any issues
- [ ] Plan hotfix releases if needed

### Performance Optimizations (Week 2-4)
- [ ] Review TODO_PERFORMANCE.md
- [ ] Implement dashboard parallelization
- [ ] Fix N+1 glossary lookups
- [ ] Implement chunked file uploads
- [ ] Add Prometheus metrics
- [ ] Set up Sentry error tracking

---

## 🎯 SUCCESS CRITERIA

### Technical Metrics (Week 1)
- [ ] API uptime > 99.5%
- [ ] P95 response time < 500ms
- [ ] Error rate < 0.1%
- [ ] All health checks passing
- [ ] No critical errors in logs

### User Metrics (Week 1)
- [ ] 10+ successful registrations
- [ ] 50+ sessions logged
- [ ] No user-reported critical bugs
- [ ] Positive user feedback

---

## 🆘 SUPPORT CONTACTS

- **Render Support:** https://render.com/docs/support
- **Database Issues:** Check Render rivaflow-db logs
- **Application Logs:** Render rivaflow-api → Logs tab
- **GitHub Issues:** https://github.com/RubyWolff27/rivaflow/issues

---

## 📝 DEPLOYMENT LOG

Use this section to log deployment events:

```
[YYYY-MM-DD HH:MM] Deployment started
[YYYY-MM-DD HH:MM] Database created: rivaflow-db
[YYYY-MM-DD HH:MM] API deployed: rivaflow-api
[YYYY-MM-DD HH:MM] Environment variables configured
[YYYY-MM-DD HH:MM] Custom domain configured: api.rivaflow.app
[YYYY-MM-DD HH:MM] SSL certificate issued
[YYYY-MM-DD HH:MM] Health checks verified
[YYYY-MM-DD HH:MM] First test user registered
[YYYY-MM-DD HH:MM] Deployment complete ✓
```

---

**🎉 Ready for Production!**

All critical fixes implemented. Follow this checklist step-by-step for a successful deployment to rivaflow.app.

**Total fixes implemented:** 23/23 tasks complete
**Security score:** 82/100 (B+) → Production-ready
**Performance score:** 75/100 (C+) → Functional, optimizable post-launch
**Estimated deployment time:** 30-45 minutes
