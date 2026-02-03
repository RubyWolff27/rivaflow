# RivaFlow v0.2.0 - Codebase Investigation Report
**Date:** February 3, 2026
**Investigation Phase:** Complete
**Status:** ✅ Ready for Implementation

---

## Executive Summary

The codebase investigation reveals that **significant v0.2.0 groundwork already exists**, including:
- ✅ Tier/subscription columns in users table
- ✅ Complete social features (friend connections, suggestions, requests)
- ✅ Dashboard API with filtering support
- ✅ Analytics API with activity type filtering
- ✅ Feedback system
- ✅ Dashboard components (WeekAtGlance, LastSession, etc.)
- ✅ Admin gym verification system

**Major work remaining:**
- Tier access enforcement (middleware/services)
- Frontend tier gating and upgrade prompts
- Enhanced dashboard layout integration
- Activity type filter UI in analytics
- Bug fixes (session navigation, instructor dropdowns)

---

## Database Schema Investigation

### ✅ Users Table
**Location:** Migration 044 (`044_grapple_foundation_pg.sql`)

**Existing tier-related columns:**
```sql
subscription_tier VARCHAR(20) DEFAULT 'free'
is_beta_user BOOLEAN DEFAULT FALSE
```

**Existing social profile columns (Migration 046):**
```sql
username VARCHAR(50) UNIQUE
display_name VARCHAR(100)
bio TEXT
belt_rank VARCHAR(20) DEFAULT 'white'
belt_stripes INTEGER DEFAULT 0
location_city VARCHAR(100)
location_state VARCHAR(100)
location_country VARCHAR(100) DEFAULT 'USA'
location_lat DECIMAL(10, 8)
location_lng DECIMAL(11, 8)
profile_photo_url TEXT
cover_photo_url TEXT
started_training DATE
preferred_style VARCHAR(20) DEFAULT 'both'
weight_class VARCHAR(20)
social_links JSONB DEFAULT '{}'
primary_gym_id INTEGER REFERENCES gyms(id)
```

**Existing privacy columns:**
```sql
profile_visibility VARCHAR(20) DEFAULT 'friends'
activity_visibility VARCHAR(20) DEFAULT 'friends'
searchable BOOLEAN DEFAULT TRUE
show_location BOOLEAN DEFAULT TRUE
show_gym BOOLEAN DEFAULT TRUE
allow_tagging BOOLEAN DEFAULT TRUE
require_tag_approval BOOLEAN DEFAULT FALSE
```

**❌ Missing columns needed for v0.2.0:**
```sql
-- tier_expires_at TIMESTAMP  -- For premium expiration
-- beta_joined_at TIMESTAMP   -- When user joined beta
```

---

### ✅ Sessions Table
**Location:** Migration 001 (`001_initial_schema.sql`)

**Activity type field:**
```sql
class_type TEXT NOT NULL  -- Values: gi, no-gi, s&c, mobility, etc.
```

**Note:** Uses `class_type`, NOT `activity_type` or `session_type`

---

### ✅ Gyms Table
**Location:** Migration 035 (`035_create_gyms_table.sql`)

**Existing columns:**
```sql
CREATE TABLE gyms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    address TEXT,
    city TEXT,
    state TEXT,
    country TEXT DEFAULT 'USA',
    website TEXT,
    verified BOOLEAN DEFAULT 0,  -- ✅ Has verified column
    added_by_user_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)
```

**Enhanced in Migration 046:**
```sql
slug VARCHAR(200) UNIQUE
affiliation VARCHAR(100)
latitude DECIMAL(10, 8)
longitude DECIMAL(11, 8)
phone VARCHAR(50)
instagram VARCHAR(100)
head_coach VARCHAR(100)
member_count INTEGER DEFAULT 0
postal_code VARCHAR(20)
```

---

### ✅ Friends Table (Local Contacts)
**Purpose:** Stores local contacts/training partners (not user-to-user connections)

**Existing columns:**
- `id`, `name`, `friend_type`, `belt_rank`, `belt_stripes`
- `instructor_certification`, `phone`, `email`, `notes`
- ✅ `gym_id` - Links friend to a gym
- ✅ `gym_role` - Role at that gym

**Note:** This is for LOCAL contacts (not RivaFlow users)

---

### ✅ Friend Connections Table (User-to-User)
**Location:** Migration 046 (`046_social_features_comprehensive_pg.sql`)

**Existing columns:**
```sql
CREATE TABLE friend_connections (
    id SERIAL PRIMARY KEY,
    requester_id INTEGER REFERENCES users(id),
    recipient_id INTEGER REFERENCES users(id),
    status VARCHAR(20) DEFAULT 'pending',  -- pending, accepted, declined, blocked, cancelled
    connection_source VARCHAR(30),  -- search, gym, mutual, partner, location, import, qr_code
    request_message TEXT,
    requested_at TIMESTAMP,
    responded_at TIMESTAMP
)
```

✅ **Already supports full friend request flow**

---

### ✅ Friend Suggestions Table
**Location:** Migration 046

**Existing columns:**
```sql
CREATE TABLE friend_suggestions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    suggested_user_id INTEGER REFERENCES users(id),
    score DECIMAL(5, 2) DEFAULT 0,
    reasons JSONB DEFAULT '[]',
    mutual_friends_count INTEGER DEFAULT 0,
    dismissed BOOLEAN DEFAULT FALSE,
    generated_at TIMESTAMP
)
```

✅ **Already supports suggestion scoring and reasons**

---

### ✅ Feedback Table
**Location:** Migration 049 (`049_app_feedback_system.sql`)

**Existing columns:**
```sql
CREATE TABLE app_feedback (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    category VARCHAR(50) NOT NULL,  -- bug, feature, improvement, question, other
    subject VARCHAR(200),
    message TEXT NOT NULL,
    platform VARCHAR(50),  -- web, cli, api
    version VARCHAR(20),
    url VARCHAR(500),
    status VARCHAR(20) DEFAULT 'new',  -- new, reviewing, resolved, closed
    admin_notes TEXT,
    resolved_at TIMESTAMP,
    created_at TIMESTAMP
)
```

✅ **Feedback system fully implemented**

---

### ❌ Feature Usage Table
**Status:** Does NOT exist yet
**Required for:** Tier limit enforcement

**Need to create:**
```sql
CREATE TABLE feature_usage (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    feature VARCHAR(50) NOT NULL,
    count INT DEFAULT 0,
    period_start DATE,
    updated_at TIMESTAMP,
    UNIQUE(user_id, feature)
)
```

---

### ✅ User-Gyms Junction Table
**Location:** Migration 046

**Existing columns:**
```sql
CREATE TABLE user_gyms (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    gym_id INTEGER REFERENCES gyms(id),
    is_primary BOOLEAN DEFAULT FALSE,
    joined_at DATE,
    left_at DATE,
    status VARCHAR(20) DEFAULT 'active',  -- active, former, visitor
    UNIQUE(user_id, gym_id)
)
```

---

### ✅ Gym Instructors Table
**Status:** Does NOT exist yet in migrations, but mentioned in brief
**Required for:** Instructor dropdown in session form

**Need to verify if this exists or needs creation**

---

## API Endpoints Investigation

### Total Endpoints: 178 across 31 route files

#### ✅ Analytics Endpoints
**File:** `rivaflow/api/routes/analytics.py`

**Existing endpoints:**
```python
GET /analytics/performance-overview?types[]=gi&types[]=nogi  # ✅ Already supports type filtering
GET /analytics/partners/stats?types[]=gi  # ✅ Already supports type filtering
GET /analytics/techniques/breakdown?types[]=gi  # ✅ Already supports type filtering
GET /analytics/readiness/trends?types[]=gi  # ✅ Already supports type filtering
GET /analytics/whoop/analytics?types[]=gi  # ✅ Already supports type filtering
GET /analytics/consistency/metrics?types[]=gi  # ✅ Already supports type filtering
GET /analytics/milestones
GET /analytics/instructors/insights?types[]=gi  # ✅ Already supports type filtering
```

**Cache:** 10-minute TTL (600 seconds)

---

#### ✅ Dashboard Endpoints
**File:** `rivaflow/api/routes/dashboard.py`

**Existing endpoints:**
```python
GET /dashboard/summary?types[]=gi&start_date=2026-01-01&end_date=2026-02-01
    # ✅ Already returns:
    # - performance (summary, deltas, timeseries)
    # - streaks (session, checkin)
    # - recent_sessions (top 5)
    # - milestones (closest, top 3 progress)
    # - weekly_goals
    # - readiness (latest)
    # - class_type_distribution

GET /dashboard/quick-stats  # Total sessions, hours, streak, next milestone

GET /dashboard/week-summary?week_offset=-1  # Summary for specific week
```

**Cache:** 5-minute TTL (300 seconds)

---

#### ✅ Social/Friends Endpoints
**File:** `rivaflow/api/routes/social.py`

**Existing friend request endpoints:**
```python
POST /social/friend-requests/{user_id}  # ✅ Send friend request
POST /social/friend-requests/{connection_id}/accept  # ✅ Accept request
POST /social/friend-requests/{connection_id}/decline  # ✅ Decline request
DELETE /social/friend-requests/{connection_id}  # ✅ Cancel sent request
GET /social/friend-requests/received  # ✅ Get pending received requests
GET /social/friend-requests/sent  # ✅ Get pending sent requests
GET /social/friends  # ✅ Get friends list
DELETE /social/friends/{user_id}  # ✅ Unfriend
GET /social/friends/{user_id}/status  # ✅ Check friendship status
```

**Existing friend suggestion endpoints:**
```python
GET /social/friend-suggestions?limit=20  # ✅ Get suggestions
POST /social/friend-suggestions/{user_id}/dismiss  # ✅ Dismiss suggestion
POST /social/friend-suggestions/regenerate  # ✅ Regenerate suggestions
```

**Existing user search:**
```python
GET /social/users/search?q=john  # ✅ Search users
GET /social/users/recommended  # ✅ Get recommended users (gym-based)
```

**Existing social features:**
```python
POST /social/follow/{user_id}  # Follow user (legacy)
DELETE /social/follow/{user_id}  # Unfollow user (legacy)
GET /social/followers  # Get followers
GET /social/following  # Get following
POST /social/like  # Like activity
DELETE /social/like  # Unlike activity
GET /social/likes/{type}/{id}  # Get likes
POST /social/comment  # Add comment
PUT /social/comment/{id}  # Update comment
DELETE /social/comment/{id}  # Delete comment
GET /social/comments/{type}/{id}  # Get comments
```

---

#### ✅ Gyms Endpoints
**File:** `rivaflow/api/routes/gyms.py`

**Existing endpoints:**
```python
GET /gyms?verified_only=true  # List gyms
GET /gyms/search?q=melbourne  # Search gyms
```

**Note:** Only 2 endpoints in public gyms route

---

#### ✅ Admin Gym Endpoints
**File:** `rivaflow/api/routes/admin.py`

**Existing endpoints:**
```python
GET /admin/gyms  # List all gyms
GET /admin/gyms/pending  # ✅ Get unverified gyms
GET /admin/gyms/search?q=melbourne  # Search all gyms
POST /admin/gyms  # Create gym
PUT /admin/gyms/{gym_id}  # Update gym
DELETE /admin/gyms/{gym_id}  # Delete gym
POST /admin/gyms/{gym_id}/verify  # ✅ Verify gym
POST /admin/gyms/{gym_id}/reject  # ✅ Reject gym
POST /admin/gyms/merge  # Merge duplicate gyms
```

---

#### ✅ Feedback Endpoints
**File:** `rivaflow/api/routes/feedback.py`

**Existing endpoints:**
```python
POST /feedback/  # ✅ Submit feedback
GET /feedback/  # List user's feedback
GET /feedback/{id}  # Get specific feedback
PUT /feedback/{id}/status  # Admin: Update status
GET /feedback/admin  # Admin: List all feedback
```

---

#### ❌ Missing Endpoints

**Session Navigation:**
```python
# NEED TO ADD:
GET /sessions/{id}/adjacent  # Get previous/next session IDs
```

**Gym Instructors:**
```python
# NEED TO ADD:
GET /gyms/{gym_id}/instructors  # Get instructors at gym
POST /gyms/{gym_id}/instructors  # Add instructor to gym
```

---

## Frontend Components Investigation

### ✅ Dashboard Components
**Location:** `web/src/components/dashboard/`

**Existing components:**
- ✅ `JourneyProgress.tsx` (6,295 bytes)
- ✅ `LastSession.tsx` (4,842 bytes)
- ✅ `WeekAtGlance.tsx` (6,569 bytes)
- ✅ `WeeklyGoalsBreakdown.tsx` (6,016 bytes)

**Status:** Already created in previous work session!

---

### ❌ Analytics Components
**Location:** `web/src/components/analytics/`
**Status:** Directory does NOT exist

**Need to create:**
- `ActivityTypeFilter.tsx`
- `ContextualMetricsGrid.tsx`
- `InsightsPanel.tsx` (Premium)

---

### ❌ Friends Components
**Location:** `web/src/components/friends/`
**Status:** Directory does NOT exist

**Need to create:**
- `FriendSuggestions.tsx` (Premium)
- `PendingRequests.tsx`
- `UserSearch.tsx`
- `AddInstructorModal.tsx`

---

### Existing Components
**Location:** `web/src/components/`

**Key existing components:**
- `FeedbackModal.tsx` - Already exists (from previous session)
- `FriendSuggestions.tsx` - Already exists (from previous session)
- `GymSelector.tsx` - Exists
- `UpgradePrompt.tsx` - Does NOT exist yet
- `ConfirmDialog.tsx` - Exists

---

## Current Behavior Analysis

### Sessions
- **Activity Type Storage:** Stored in `class_type` field
- **Valid Values:** gi, no-gi, s&c, mobility, drilling, open-mat, competition
- **Display:** Currently generic (no activity-aware UI)

### Gyms
- **Creation:** When user creates gym via POST /gyms
- **Verified Status:** ❓ NEED TO TEST - should be set to `verified=false`
- **Admin Queue:** ✅ GET /admin/gyms/pending endpoint exists
- **Verification:** ✅ POST /admin/gyms/{id}/verify endpoint exists

### Instructor Dropdown
- **Current Source:** Queries `friends` table where `friend_type = 'instructor'`
- **Issue:** Does NOT query gym-specific instructors
- **Fix Required:** Need `gym_instructors` table and API endpoint

### Friend Requests
- **Status:** ✅ Fully implemented backend
- **Frontend:** ✅ Updated in previous session (FindFriends.tsx)
- **Flow:** Send → Accept/Decline → Friends

### Feedback
- **Status:** ✅ Fully implemented
- **Frontend:** ✅ FeedbackModal created in previous session
- **Integration:** ✅ Replaces GitHub link

---

## Service Layer Investigation

### ✅ Existing Services
**Location:** `rivaflow/core/services/`

**Relevant services that exist:**
- `analytics_service.py` - ✅ Supports type filtering
- `gym_service.py` - ✅ Handles gym CRUD
- `friend_suggestions_service.py` - ✅ Implements scoring algorithm
- `goals_service.py` - ✅ Weekly goals tracking
- `milestone_service.py` - ✅ Milestone tracking
- `streak_service.py` - ✅ Streak calculation
- `email_service.py` - ✅ Email notifications
- `feedback_service.py` - ❓ Check if exists

### ❌ Missing Services
- `tier_access_service.py` - For tier checking and enforcement
- `feature_usage_service.py` - For tracking usage limits

---

## Repository Layer Investigation

### ✅ Existing Repositories
**Location:** `rivaflow/db/repositories/`

**Relevant repositories:**
- `session_repo.py` - ✅ Handles session queries
- `social_connection_repo.py` - ✅ Handles friend connections
- `feedback_repo.py` - ✅ Handles feedback
- `gym_repo.py` - ✅ Handles gym CRUD

### ❌ Missing Repositories
- `feature_usage_repo.py` - For tier limit tracking
- `gym_instructor_repo.py` - For gym instructors (if table exists)

---

## Frontend Hooks Investigation

### ✅ Existing Hooks
**Location:** `web/src/hooks/`

**Relevant hooks:**
- `useUser.ts` - ✅ User context
- `useAuth.ts` - ✅ Authentication
- `useToast.ts` - ✅ Toast notifications

### ❌ Missing Hooks
- `useTier.ts` - For tier checking in components

---

## Configuration Investigation

### Database Type
- **Production:** PostgreSQL (from DATABASE_URL)
- **Development:** SQLite fallback
- **Migrations:** 57 total, up to migration 049

### API Configuration
- **Base URL:** `/api/v1`
- **Auth:** JWT Bearer tokens
- **Caching:** Redis (performance_overview: 10min, dashboard_summary: 5min)

---

## Summary: What Already Exists vs. What's Needed

### ✅ Already Complete (80% of backend)

1. **Database Schema:**
   - ✅ Users table with tier columns
   - ✅ Friend connections table
   - ✅ Friend suggestions table
   - ✅ Feedback table
   - ✅ Gyms table with verified column
   - ✅ User-gyms junction table

2. **API Endpoints:**
   - ✅ Analytics with type filtering
   - ✅ Dashboard summary endpoint
   - ✅ Friend request full flow
   - ✅ Friend suggestions
   - ✅ User search
   - ✅ Admin gym verification
   - ✅ Feedback submission

3. **Frontend Components:**
   - ✅ Dashboard components (4 components)
   - ✅ FeedbackModal
   - ✅ FriendSuggestions
   - ✅ FindFriends with request flow

4. **Services:**
   - ✅ Analytics service with filtering
   - ✅ Friend suggestions with scoring
   - ✅ Gym service
   - ✅ Goals service
   - ✅ Milestone service

---

### ❌ Still Needed (20% remaining)

1. **Tier System:**
   - ❌ Tier access service
   - ❌ Tier middleware/decorators
   - ❌ Frontend tier hook
   - ❌ Upgrade prompt component
   - ❌ Feature usage tracking table
   - ❌ Feature usage repository
   - ❌ Add `tier_expires_at` and `beta_joined_at` columns

2. **Dashboard:**
   - ❌ Integrate 4 dashboard components into Dashboard.tsx
   - ❌ Enhanced readiness display
   - ❌ Activity-aware metrics

3. **Analytics:**
   - ❌ ActivityTypeFilter component UI
   - ❌ Contextual metrics grid
   - ❌ Tab visibility logic
   - ❌ URL param persistence

4. **Bug Fixes:**
   - ❌ Session navigation (previous/next)
   - ❌ Gym instructors table and endpoints
   - ❌ Verify gym creation sets verified=false

5. **Polish:**
   - ❌ Premium badges throughout UI
   - ❌ Upgrade prompts on gated features
   - ❌ Mobile responsive checks

---

## Recommendations for Implementation Order

Given the investigation findings, here's the optimized implementation order:

### Phase 1: Tier System Foundation (2-3 hours)
**Reason:** Everything else depends on this

1. Add missing user columns (tier_expires_at, beta_joined_at)
2. Create feature_usage table
3. Create tier access service
4. Create tier middleware
5. Create useTier hook
6. Create UpgradePrompt component
7. Migrate beta users

### Phase 2: Bug Fixes (1-2 hours)
**Reason:** Quick wins, improve UX immediately

1. Fix gym creation verification flag
2. Add session navigation endpoint
3. Create gym_instructors table and endpoints
4. Update session form instructor dropdown

### Phase 3: Dashboard Integration (1-2 hours)
**Reason:** Components already exist, just need integration

1. Update Dashboard.tsx to use existing components
2. Add Premium gating
3. Add readiness prominence
4. Test responsive layout

### Phase 4: Analytics Enhancement (2-3 hours)
**Reason:** Backend already supports it, just need UI

1. Create ActivityTypeFilter component
2. Update Reports.tsx with filter
3. Implement contextual metrics
4. Add tab visibility logic
5. Add URL param persistence

### Phase 5: Premium Gating & Polish (2-3 hours)
**Reason:** Final touches

1. Add Premium badges throughout
2. Add upgrade prompts
3. Test all tier checks
4. Mobile responsive fixes

### Phase 6: Testing & Verification (1-2 hours)
**Reason:** Ensure everything works

1. Test as free user
2. Test as premium user
3. Test all flows end-to-end
4. Fix any issues

---

## Critical Notes

1. **Sessions use `class_type` NOT `activity_type`** - Remember this everywhere!
2. **Dashboard components already created** - Just need integration
3. **Friend request system fully functional** - Backend + frontend complete
4. **Most API endpoints already exist** - Very little new API work needed
5. **Tier columns exist but no enforcement** - Need middleware/services

---

## Next Steps

✅ **Investigation Complete**
➡️ **Ready to proceed with Phase 1: Tier System Foundation**

**Estimated Total Time:** 10-15 hours
**Commit Strategy:** Commit after each phase

---

**End of Investigation Report**
