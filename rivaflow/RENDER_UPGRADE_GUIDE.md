# Render Account Upgrade Guide

## Current Status: Free Tier ✅

Your RivaFlow deployment is currently on Render's **Free Tier** and should work fine for beta testing.

## When to Upgrade

### ⚠️ You NEED to upgrade when:

1. **Database Size Limit (1 GB)**
   - Free tier PostgreSQL: 1 GB storage
   - Check current size: `SELECT pg_database_size('rivaflow') / 1024 / 1024 AS size_mb;`
   - With pgvector embeddings, you'll hit this faster
   - **Action**: Upgrade to Starter ($7/month) for 10 GB

2. **Instance Sleep (15 min inactivity)**
   - Free web services sleep after 15 minutes of inactivity
   - Cold starts take 30-60 seconds
   - **Impact**: First request after sleep will be slow
   - **Action**: Upgrade to Starter ($7/month) for always-on

3. **Build Minutes (750 hours/month)**
   - Free tier: 500 hours/month shared across all services
   - Each deploy uses ~2-5 minutes
   - ML dependencies (sentence-transformers) increase build time
   - **Action**: Monitor in Render dashboard

### 💡 Consider upgrading when:

4. **Multiple Active Beta Users (>10)**
   - Concurrent requests may be slow on free tier (512 MB RAM, 0.1 CPU)
   - **Action**: Upgrade to Starter for 512 MB RAM + 0.5 CPU

5. **High Grapple Usage**
   - If users hit rate limits frequently
   - If chat responses are slow
   - **Check**: `/api/v1/admin/grapple/stats/global`

6. **Data Transfer (100 GB/month)**
   - Free tier: 100 GB bandwidth
   - With media uploads + chat traffic, could be exceeded
   - **Action**: Monitor in Render dashboard

## Render Pricing Tiers

### Free Tier (Current)
- **Web Service**: 512 MB RAM, 0.1 CPU
- **Database**: 1 GB storage, 90-day expiration
- **Bandwidth**: 100 GB/month
- **Build Minutes**: 500 hours/month
- **Sleeps after**: 15 minutes inactivity
- **Cost**: $0/month

### Starter Tier ($7/month)
- **Web Service**: 512 MB RAM, 0.5 CPU
- **Always-on** (no sleep)
- Same bandwidth/build limits
- **Cost**: $7/month per service

### PostgreSQL Starter ($7/month)
- **Storage**: 10 GB
- **No expiration**
- **Backups**: Daily
- **Cost**: $7/month

### Total for Production-Ready Setup
- Web Service Starter: $7/month
- PostgreSQL Starter: $7/month
- **Total**: $14/month

## Monitoring Dashboard

Use these admin endpoints to monitor when you need to upgrade:

```bash
# Global usage stats
GET /api/v1/admin/grapple/stats/global?days=30

# Cost projections
GET /api/v1/admin/grapple/stats/projections

# Provider reliability
GET /api/v1/admin/grapple/stats/providers

# Top users
GET /api/v1/admin/grapple/stats/users

# System health
GET /api/v1/admin/grapple/health
```

## Grapple Cost Projections

Based on Groq free tier (14,400 requests/day):
- **Beta usage** (30 msg/hr per user): ~720 messages/day per active user
- **5 active users**: 3,600 messages/day = **Well within free tier**
- **20 active users**: 14,400 messages/day = **At free tier limit**

**When to worry**: If you have 20+ active beta users chatting daily.

**Current cost**: $0/month (Groq free tier)
**Projected cost at scale**: ~$0-5/month (Together AI fallback)

## Database Size Estimates

With current schema + Grapple:
- **Users**: ~1 KB per user
- **Sessions**: ~100 KB per session (with logs)
- **Chat sessions**: ~50 KB per chat session
- **Chat messages**: ~2 KB per message
- **Token logs**: ~500 bytes per log entry
- **pgvector embeddings**: ~1.5 KB per knowledge base entry

**Example**: 100 users, 1000 training sessions, 500 chat sessions with 5000 messages
- Users: 100 KB
- Sessions: 100 MB
- Chat: 35 MB
- Logs: 2.5 MB
- **Total**: ~140 MB (well under 1 GB limit)

**You'll hit 1 GB** when:
- 1000+ training sessions with media
- 5000+ chat sessions
- 50,000+ chat messages
- Large BJJ knowledge base (10,000+ entries)

## Action Items

### Monitor Weekly
1. Check database size in Render dashboard
2. Review `/admin/grapple/stats/global` for usage trends
3. Check Groq API dashboard for request counts

### Upgrade Triggers
- **Database >800 MB**: Upgrade PostgreSQL to Starter
- **Frequent cold starts**: Upgrade web service to Starter
- **>15 active beta users**: Consider both upgrades

### Current Recommendation
**Stay on free tier** until you see:
- Database approaching 800 MB
- 15+ daily active beta users
- Consistent user complaints about cold starts

You'll likely get 2-3 months of beta testing on free tier before needing to upgrade.
