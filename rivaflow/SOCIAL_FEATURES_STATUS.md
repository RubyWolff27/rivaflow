# Social Features Implementation Status

**Decision:** DEFERRED until 100+ monthly active users

**Date:** February 1, 2026
**Reason:** Not worth effort at current scale - better to focus on core training features

---

## What's Been Implemented (Phase 1)

### ✅ Database Migration 046
**File:** `db/migrations/046_social_features_comprehensive_pg.sql`
**Status:** Committed and will deploy
**Decision:** **KEEP** - Migration is safe and adds useful fields

**What it adds:**
- Enhanced user profile fields (username, display_name, belt_rank, location)
- Privacy settings columns (even if not enforced yet, schema is ready)
- Enhanced gyms table (slug, affiliation, coordinates for future use)
- Social tables (friend_connections, activity_feed, etc.) - **NOT USED YET**

**Why keep it:**
- Safe migration (all `IF NOT EXISTS`, won't break anything)
- Adds genuinely useful fields: username, belt_rank, location
- Future-ready when we DO implement social features
- Auto-generates usernames from emails for existing users
- Small database impact (~10 new columns + 7 empty tables)

### ✅ Social Connection Repository
**File:** `db/repositories/social_connection_repo.py`
**Status:** Committed but **NOT USED ANYWHERE**
**Decision:** **OPTIONAL** - Can keep or remove

**What it does:**
- Friend request/accept/decline logic
- Blocking functionality
- Friend list queries

**Options:**
1. **Keep it** - Code is ready when needed, not using resources
2. **Remove it** - Cleaner codebase, no unused code

---

## What's NOT Implemented (Deferred)

### ❌ API Endpoints (Not Built)
- No REST APIs for social features
- No authentication/authorization for social endpoints
- No rate limiting for search

**Why deferred:**
- No point exposing APIs if frontend doesn't use them
- Security surface area increases unnecessarily
- Maintenance burden for unused endpoints

### ❌ Frontend UI (Not Built)
- No profile pages
- No friend discovery/search
- No friend requests UI
- No activity feed

**Why deferred:**
- Core value prop with small user base is low
- Development time better spent on training features
- UX complexity (privacy settings, blocking, etc.) not justified

### ❌ Suggestion Algorithm (Not Built)
- No friend suggestion scoring
- No background jobs
- No partner text matching

**Why deferred:**
- Overkill for <100 users (just search manually)
- Complex algorithm has little value at small scale

---

## Recommendation

### Keep:
- ✅ **Migration 046** - Adds genuinely useful profile fields (username, belt_rank)
- ✅ **social_connection_repo.py** - Ready when needed, no harm in keeping

### Don't Implement Yet:
- ❌ API endpoints for social features
- ❌ Frontend UI (profiles, friend discovery, feed)
- ❌ Suggestion algorithm
- ❌ Background jobs

### When to Revisit:
**Triggers:**
- 100+ monthly active users
- Users actively asking "who else from my gym uses this?"
- Multiple gyms with 5+ users each
- Users manually sharing profiles outside the app

**Early Signals:**
- Users putting gym name in bio to find each other
- Discord/Slack messages asking about connecting with training partners
- Feature requests for "see who else trains at X gym"

---

## Current State After Deployment

**Database:**
- New tables exist but are empty: friend_connections, activity_feed, etc.
- New columns exist: users.username, users.belt_rank, users.location_*
- Auto-generated usernames for existing users (from email)

**Backend:**
- social_connection_repo.py exists but is not imported/used anywhere
- No API routes registered
- No services using the social schema

**Frontend:**
- No UI changes
- No new pages
- No impact on existing features

**Impact:**
- ✅ Zero impact on existing functionality
- ✅ Existing users can continue using app normally
- ✅ Database slightly larger but negligible
- ✅ Ready to build on when user base justifies it

---

## If You Want to Clean Up

**Option 1: Keep Everything (Recommended)**
- No action needed
- Migration is safe and future-ready
- Repo code isn't hurting anything

**Option 2: Remove Unused Repository**
```bash
git rm db/repositories/social_connection_repo.py
git commit -m "Remove unused social connection repo (deferred feature)"
git push
```

**Option 3: Roll Back Everything (Not Recommended)**
- Would need to create rollback migration to drop tables/columns
- Risk of migration conflicts
- Better to just leave it and ignore it

---

## When Implementing Later

**Pickup point:**
1. Review migration 046 (schema already exists ✅)
2. Review social_connection_repo.py (already built ✅)
3. Implement Phase 2: API endpoints (see PRD)
4. Implement Phase 3: Frontend UI (see PRD)
5. Implement Phase 4: Suggestion algorithm (see PRD)

**Estimate:** ~40 hours to go from current state to production-ready social features

**See:** `FUTURE_RELEASES.md` for full roadmap entry
