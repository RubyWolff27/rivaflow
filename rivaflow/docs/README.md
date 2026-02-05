# RivaFlow Documentation

## Quick Links

### Live Services
- **Frontend:** https://rivaflow.app
- **API:** https://api.rivaflow.app
- **API Docs:** https://api.rivaflow.app/docs
- **Health Check:** https://api.rivaflow.app/health

### Documentation Files

1. **[DEPLOYMENT_SUMMARY_2026-02-05.md](./DEPLOYMENT_SUMMARY_2026-02-05.md)**
   - Complete deployment timeline and architecture
   - All issues fixed during deployment
   - Environment configuration
   - Troubleshooting guide
   - **Read this first for full context**

2. **[API_ENDPOINT_AUDIT.md](./API_ENDPOINT_AUDIT.md)**
   - Comprehensive API endpoint testing results
   - All 18+ endpoints verified working
   - Frontend code audit (all direct fetch calls fixed)
   - Issues found and resolved

3. **[fix_sequences_manual.sql](./fix_sequences_manual.sql)**
   - PostgreSQL sequence reset script
   - Use if you encounter duplicate key errors
   - Run in Render database shell

4. **[../DEPLOYMENT_CHECKLIST.md](../DEPLOYMENT_CHECKLIST.md)**
   - Original deployment checklist
   - Pre/post deployment tasks
   - Success criteria

## Architecture at a Glance

```
┌─────────────────────┐       ┌──────────────────────┐       ┌─────────────────┐
│   rivaflow.app      │ ───>  │  api.rivaflow.app    │ ───>  │  PostgreSQL DB  │
│  React/TypeScript   │       │  FastAPI/Python 3.11 │       │  Render Managed │
│  Render Static Site │       │  Render Web Service  │       │  PostgreSQL 16  │
└─────────────────────┘       └──────────────────────┘       └─────────────────┘
```

## Tech Stack

- **Frontend:** React 18, TypeScript, Vite, TailwindCSS
- **Backend:** Python 3.11, FastAPI, psycopg2
- **Database:** PostgreSQL 16
- **Hosting:** Render.com
- **DNS:** Cloudflare
- **Auth:** JWT with refresh tokens

## Quick Troubleshooting

### Dashboard shows 404 errors
- **Cause:** Browser cache
- **Fix:** Hard refresh (Ctrl+Shift+R) or incognito window

### Duplicate key error on registration
- **Cause:** PostgreSQL sequences out of sync
- **Fix:** Run `fix_sequences_manual.sql` in database shell

### CORS errors
- **Cause:** Domain not in ALLOWED_ORIGINS
- **Fix:** Add domain to API environment variable in Render

## Git Commits (Feb 5, 2026)

Key commits from deployment session:
```
fb48ec5 - Add comprehensive deployment documentation
0a01444 - Fix JourneyProgress to use API client instead of direct fetch
6f64585 - Fix Friends page to handle API response object structure
4e51b00 - Fix Dashboard to use composite_score instead of overall_score
6cfee73 - Fix vite.config.ts syntax error
484a1a4 - Fix Dashboard readiness API call to use correct endpoint
```

## Environment Variables

### API Service
- `ENV=production`
- `SECRET_KEY=<32+ chars>`
- `DATABASE_URL=<from Render>`
- `ALLOWED_ORIGINS=https://rivaflow.app,...`

### Frontend Service
- `VITE_API_URL=https://api.rivaflow.app/api/v1`

## Support

- **Render Logs:** Dashboard → Service → Logs tab
- **Database Shell:** Dashboard → Database → Connect
- **GitHub:** https://github.com/RubyWolff27/rivaflow

---

**Last Updated:** February 5, 2026
**Status:** ✅ LIVE IN PRODUCTION
