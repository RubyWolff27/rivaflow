# RivaFlow v0.2.0 Deployment Guide

Complete guide for deploying RivaFlow to production on Render.com.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Variables](#environment-variables)
3. [Render Setup](#render-setup)
4. [Custom Domain Configuration](#custom-domain-configuration)
5. [Database Setup](#database-setup)
6. [Post-Deployment Checks](#post-deployment-checks)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

- GitHub account with rivaflow repository
- Render.com account (free tier works)
- Custom domain (optional, for production)
- SendGrid account for emails (optional)
- Redis instance for caching (optional)

---

## Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | JWT token secret (32+ chars) | Generate: `python -c 'import secrets; print(secrets.token_urlsafe(32))'` |
| `DATABASE_URL` | PostgreSQL connection string | Auto-populated by Render |
| `ENV` | Environment name | `production` |

### Recommended Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `ALLOWED_ORIGINS` | CORS allowed origins | `https://rivaflow.com,https://www.rivaflow.com` |
| `REDIS_URL` | Redis connection string | Auto-populated by Render |
| `SENDGRID_API_KEY` | Email API key | From SendGrid dashboard |

---

## Render Setup

### 1. Create New Web Service

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Select **rivaflow** repository
5. Configure service:

```yaml
Name: rivaflow-api
Region: Oregon (or closest to your users)
Branch: main
Runtime: Python 3
Build Command: bash build.sh
Start Command: uvicorn rivaflow.api.main:app --host 0.0.0.0 --port $PORT
```

### 2. Set Environment Variables

In service settings → Environment:

```bash
# Required
SECRET_KEY=<click "Generate Value">
ENV=production
PYTHON_VERSION=3.11.0

# Database (connect in next step)
DATABASE_URL=<auto-populated>

# CORS
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### 3. Create PostgreSQL Database

1. In Render dashboard, click **"New +"** → **"PostgreSQL"**
2. Configure:
   - Name: `rivaflow-db`
   - Region: Same as web service
   - Plan: Free (or paid for production)
3. Click **"Create Database"**
4. Go back to web service → Environment
5. Connect DATABASE_URL to `rivaflow-db`

### 4. Optional: Add Redis

1. Click **"New +"** → **"Redis"**
2. Configure:
   - Name: `rivaflow-cache`
   - Region: Same as other services
   - Plan: Free
3. Connect REDIS_URL to web service

### 5. Deploy

1. Click **"Manual Deploy"** → **"Deploy latest commit"**
2. Watch build logs for:
   ```
   ========================================================================
   RivaFlow Build v0.2.0 - NO AI DEPENDENCIES
   ✓ VERSION file found: 0.2.0
   ========================================================================
   ```
3. Wait for "Live" status (green checkmark)

---

## Custom Domain Configuration

### 1. Add Domain in Render

1. Go to service → **Settings** → **Custom Domains**
2. Click **"Add Custom Domain"**
3. Enter your domain (e.g., `api.rivaflow.com`)
4. Render provides DNS records

### 2. Configure DNS

Add these records in your DNS provider:

```
Type: CNAME
Name: api (or @ for root domain)
Value: <your-render-url>.onrender.com
TTL: 3600
```

### 3. Enable SSL

Render automatically provisions SSL certificates via Let's Encrypt.
Wait 5-10 minutes for certificate issuance.

### 4. Update ALLOWED_ORIGINS

Update environment variable:

```bash
ALLOWED_ORIGINS=https://api.rivaflow.com,https://rivaflow.com
```

---

## Database Setup

### Fresh Database

The build script automatically runs `init_db()` which:
- Creates all tables
- Runs all 54 migrations
- Sets up indexes and constraints

### Verify Database

1. Go to `rivaflow-db` in Render dashboard
2. Click **"Connect"** → **External Connection**
3. Use provided credentials with psql:

```bash
psql postgresql://user:pass@host/database
```

4. Check tables:

```sql
\dt
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM sessions;
```

---

## Post-Deployment Checks

### 1. Health Check

```bash
curl https://your-domain.com/health
```

Expected response:

```json
{
  "status": "healthy",
  "service": "rivaflow-api",
  "version": "0.2.0",
  "database": "connected"
}
```

### 2. API Documentation

Visit: `https://your-domain.com/docs`

Verify:
- Swagger UI loads
- All endpoints visible
- Can test /health endpoint

### 3. User Registration

```bash
curl -X POST https://your-domain.com/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!",
    "first_name": "Test",
    "last_name": "User"
  }'
```

Expected: 201 Created with user data and tokens

### 4. Security Headers

```bash
curl -I https://your-domain.com/health
```

Verify headers present:
- `Strict-Transport-Security`
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Content-Security-Policy`

---

## Troubleshooting

### Build Fails: "No module named 'rivaflow.db'"

**Cause:** Old cached build or package configuration issue

**Solution:**
1. Go to Settings → Build & Deploy
2. Click **"Clear build cache"**
3. Manual Deploy → Deploy latest commit

### Build Fails: "SECRET_KEY required"

**Cause:** Environment variable not set

**Solution:**
1. Go to Environment tab
2. Add `SECRET_KEY` variable
3. Click "Generate Value" button
4. Save and redeploy

### Database Connection Fails

**Cause:** DATABASE_URL not connected or wrong format

**Solution:**
1. Verify rivaflow-db is created and "Available"
2. In web service Environment tab
3. Click "+ Add" next to DATABASE_URL
4. Select "From Database: rivaflow-db"
5. Save and redeploy

### CORS Errors in Browser

**Cause:** ALLOWED_ORIGINS not set or incorrect

**Solution:**
1. Add/update ALLOWED_ORIGINS environment variable
2. Include your frontend domain with protocol
3. Example: `https://rivaflow.com,https://www.rivaflow.com`
4. Save and redeploy

### 503 Service Unavailable

**Cause:** Application failed to start or health check failing

**Solution:**
1. Check logs for startup errors
2. Verify all required env vars set
3. Check database connectivity
4. Review build logs for errors

---

## Monitoring & Maintenance

### View Logs

```bash
# Real-time logs
render logs -f rivaflow-api

# Or in dashboard: Events → View Logs
```

### Health Monitoring

Set up external monitoring:
- UptimeRobot (free)
- Pingdom
- StatusCake

Monitor endpoint: `https://your-domain.com/health`

### Database Backups

Render automatically backs up PostgreSQL databases daily (paid plans).

Manual backup:

```bash
pg_dump DATABASE_URL > backup_$(date +%Y%m%d).sql
```

### Update Deployment

```bash
# Push code to main branch
git push origin main

# Render auto-deploys if enabled
# Or: Dashboard → Manual Deploy
```

---

## Support

- **Documentation:** https://github.com/RubyWolff27/rivaflow/tree/main/docs
- **Issues:** https://github.com/RubyWolff27/rivaflow/issues
- **Render Docs:** https://render.com/docs

---

**Deployment Checklist:**

- [ ] Render account created
- [ ] PostgreSQL database created
- [ ] SECRET_KEY generated (32+ chars)
- [ ] ENV=production
- [ ] ALLOWED_ORIGINS set for your domain
- [ ] Build succeeds with v0.2.0 banner
- [ ] /health returns 200 OK
- [ ] User registration works
- [ ] User login works
- [ ] Custom domain configured (optional)
- [ ] SSL certificate issued (optional)
- [ ] Monitoring set up (recommended)

---

**🎉 Ready for Beta Users!**
