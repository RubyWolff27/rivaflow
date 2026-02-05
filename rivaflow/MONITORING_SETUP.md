# Production Monitoring Setup Guide

## Overview
This guide covers setting up production monitoring for RivaFlow using Sentry (error tracking) and UptimeRobot (uptime monitoring).

---

## 1. Sentry Error Tracking

### Setup Steps

1. **Create Sentry Account** (if not exists)
   - Go to https://sentry.io
   - Sign up for free tier (5,000 errors/month)
   - Create organization: "RivaFlow"

2. **Create Backend Project**
   - Click "Create Project"
   - Platform: Python
   - Name: "rivaflow-api"
   - Copy DSN (Data Source Name)

3. **Install Sentry SDK**
   ```bash
   pip install sentry-sdk[fastapi]
   ```

4. **Add to requirements.txt**
   ```
   sentry-sdk[fastapi]==1.40.0
   ```

5. **Configure Sentry in Backend**

   Add to `/rivaflow/api/main.py` (after imports):
   ```python
   import sentry_sdk
   from sentry_sdk.integrations.fastapi import FastApiIntegration
   from sentry_sdk.integrations.starlette import StarletteIntegration

   # Initialize Sentry (only in production)
   if settings.IS_PRODUCTION and os.getenv("SENTRY_DSN"):
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
           # Filter out sensitive data
           before_send=lambda event, hint: event if not _contains_sensitive_data(event) else None,
       )
       logger.info("Sentry error tracking enabled")
   ```

6. **Add Environment Variable to Render**
   - Render Dashboard → rivaflow-api → Environment
   - Add: `SENTRY_DSN=<your-sentry-dsn>`

7. **Test Sentry Integration**
   ```python
   # Add test endpoint (remove after verification)
   @app.get("/sentry-test")
   def test_sentry():
       1 / 0  # Intentional error
       return {"status": "ok"}
   ```

   Then visit: `https://api.rivaflow.app/sentry-test`
   Check Sentry dashboard for error report.

---

## 2. Frontend Error Tracking (Sentry)

1. **Create Frontend Project in Sentry**
   - Platform: React
   - Name: "rivaflow-web"
   - Copy DSN

2. **Install Sentry SDK**
   ```bash
   cd web/
   npm install @sentry/react --save
   ```

3. **Configure in ErrorBoundary**

   Update `/web/src/components/ErrorBoundary.tsx`:
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

   // In componentDidCatch:
   componentDidCatch(error: Error, errorInfo: ErrorInfo) {
     console.error('ErrorBoundary caught:', error, errorInfo);

     if (import.meta.env.PROD) {
       Sentry.captureException(error, { extra: errorInfo });
     }

     this.setState({ error, errorInfo });
   }
   ```

4. **Add Environment Variable**
   - Render Dashboard → rivaflow-web → Environment
   - Add: `VITE_SENTRY_DSN=<your-frontend-sentry-dsn>`

---

## 3. UptimeRobot Monitoring

### Setup Steps

1. **Create UptimeRobot Account**
   - Go to https://uptimerobot.com
   - Sign up for free tier (50 monitors)

2. **Create API Monitor**
   - Click "Add New Monitor"
   - Monitor Type: HTTP(s)
   - Friendly Name: "RivaFlow API"
   - URL: `https://api.rivaflow.app/health`
   - Monitoring Interval: 5 minutes
   - Monitor Timeout: 30 seconds
   - Alert When Down For: 2 checks (10 minutes)

3. **Create Frontend Monitor**
   - Monitor Type: HTTP(s)
   - Friendly Name: "RivaFlow Web"
   - URL: `https://rivaflow.app`
   - Monitoring Interval: 5 minutes

4. **Configure Alert Contacts**
   - Settings → Alert Contacts
   - Add your email
   - Optional: Add Slack/Discord webhook

5. **Configure Public Status Page** (Optional)
   - My Settings → Add New Public Status Page
   - Select monitors: RivaFlow API, RivaFlow Web
   - Customize URL: `rivaflow.uptimerobot.com`
   - Share with beta users

---

## 4. Database Monitoring

### Setup in Render Dashboard

1. **Enable Database Metrics**
   - Render Dashboard → rivaflow-db → Metrics
   - Monitor:
     - Connection count (alert if >18/20)
     - Query duration P95 (alert if >500ms)
     - Disk usage (alert at 80%)

2. **Set up Alerts**
   - Render Dashboard → rivaflow-db → Settings → Alerts
   - Add email notification for:
     - High CPU usage (>80%)
     - High memory usage (>80%)
     - Disk space critical (<20%)

---

## 5. Application Performance Monitoring (APM)

### Option 1: Sentry Performance (Recommended)
Already included in Sentry setup above with `traces_sample_rate=0.1`.

Features:
- API endpoint performance tracking
- Database query performance
- Frontend page load times
- User interaction tracking

### Option 2: New Relic (Alternative)
If you need more detailed APM:

1. Sign up: https://newrelic.com (free tier: 100GB/month)
2. Install agent: `pip install newrelic`
3. Configure: `newrelic.ini`
4. Add to Render env: `NEW_RELIC_LICENSE_KEY`

---

## 6. Log Aggregation

### Render Logs (Built-in)
- Access: Render Dashboard → Service → Logs
- Retention: 7 days (free tier)
- Features:
  - Real-time log streaming
  - Search and filter
  - Download logs

### Papertrail (Optional)
For longer retention:

1. Sign up: https://papertrailapp.com (free: 50MB/month)
2. Get log destination: `logs<N>.papertrailapp.com:<PORT>`
3. Add to Render:
   - Settings → Logging → Papertrail
   - Enter log destination

---

## 7. Monitoring Checklist

### Pre-Launch
- [ ] Sentry backend configured and tested
- [ ] Sentry frontend configured
- [ ] UptimeRobot monitors created (API + Web)
- [ ] Alert contacts configured
- [ ] Test alert delivery (trigger intentional error)

### Post-Launch (Week 1)
- [ ] Review Sentry errors daily
- [ ] Monitor uptime metrics (target: >99.5%)
- [ ] Check database connection usage
- [ ] Review API response times (P95 < 500ms)
- [ ] Monitor error rates (target: <0.1%)

### Ongoing
- [ ] Weekly Sentry error review
- [ ] Monthly uptime report
- [ ] Quarterly performance review
- [ ] Update alert thresholds based on actual usage

---

## 8. Monitoring Dashboard

### Key Metrics to Track

**Availability Metrics:**
- API uptime: Target >99.5%
- Frontend uptime: Target >99.9%
- Average response time: Target <200ms

**Error Metrics:**
- Error rate: Target <0.1%
- 4xx errors: Monitor for API misuse
- 5xx errors: Critical - investigate immediately

**Performance Metrics:**
- P50 response time: Target <100ms
- P95 response time: Target <500ms
- P99 response time: Target <1s

**User Metrics:**
- Active users (DAU/MAU)
- Session duration
- Page load time
- API calls per user

---

## 9. Alerting Strategy

### Critical Alerts (Page Immediately)
- API down for >5 minutes
- Database connection failure
- Error rate >1%
- Multiple 5xx errors in 5 minutes

### High Priority (Notify Within Hour)
- API response time >2s (P95)
- Database connections >18/20
- Disk usage >80%
- Memory usage >85%

### Medium Priority (Daily Digest)
- Error rate 0.1% - 1%
- New error types
- Performance degradation
- Failed background jobs

---

## 10. Emergency Procedures

### If API Goes Down:
1. Check Sentry for recent errors
2. Check Render logs
3. Verify database connectivity
4. Check recent deployments (rollback if needed)
5. Post status update to beta users

### If Database Issues:
1. Check Render database metrics
2. Check for long-running queries
3. Check connection pool usage
4. Restart database if needed (Render dashboard)
5. Contact Render support if persistent

---

## Estimated Costs (Free Tiers)

- **Sentry**: Free (5,000 errors/month) ✅
- **UptimeRobot**: Free (50 monitors, 5-min intervals) ✅
- **Render Logs**: Included ✅
- **Total**: $0/month for beta

Upgrade when needed:
- Sentry Team: $26/month (50,000 errors)
- UptimeRobot Pro: $7/month (1-min intervals)

---

## Configuration Files Created

- `.github/workflows/test.yml` - CI/CD testing
- `.github/workflows/security.yml` - Security scans
- `.github/workflows/deploy.yml` - Safe deployments
- `MONITORING_SETUP.md` - This guide

---

## Next Steps

1. Set up Sentry accounts (backend + frontend)
2. Add Sentry DSNs to Render environment variables
3. Deploy updated code with Sentry integration
4. Create UptimeRobot monitors
5. Test all alerts
6. Monitor for first 24 hours actively

---

**Status**: ✅ Documentation complete, ready to implement
**Estimated Setup Time**: 1.5 hours
**Maintenance**: 15 minutes/week
