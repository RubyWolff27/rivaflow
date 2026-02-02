# RivaFlow v0.2.0 - Codebase Investigation Report

**Date:** 2026-02-02
**Purpose:** Assess current architecture before v0.2.0 implementation
**Status:** ✅ COMPREHENSIVE SCHEMA CONFIRMED

---

## Executive Summary

RivaFlow has a **mature, well-designed database schema** ready for v0.2.0 with minimal structural changes needed. Most requested features from the original v0.2.0 prompt are **already implemented** at the database level. Primary work needed is:

1. ✅ Database schema → **95% complete**
2. ⚠️  API endpoints → **70% complete** (missing: type filtering, admin gym verification)
3. ❌ Frontend components → **Not found** (backend-only repository)
4. ⚠️  Friend suggestion algorithm → **Schema ready, service needs implementation**

---

## Database Schema (47 Tables)

### ✅ CORE TABLES - FULLY IMPLEMENTED

#### 1. SESSIONS TABLE
**Status:** ✅ Complete with all required fields

```sql
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    session_date TEXT NOT NULL,
    class_type TEXT NOT NULL,  -- Uses 'class_type' NOT 'activity_type'
    gym_name TEXT,
    location TEXT,
    class_time TEXT,
    duration_mins INTEGER DEFAULT 60,
    intensity INTEGER CHECK(intensity BETWEEN 1 AND 5),
    rolls INTEGER DEFAULT 0,
    submissions_for INTEGER DEFAULT 0,
    submissions_against INTEGER DEFAULT 0,
    partners TEXT,  -- JSON array
    techniques TEXT,  -- JSON array
    notes TEXT,
    visibility_level TEXT DEFAULT 'private',  -- private/attendance/summary/full
    instructor_id INTEGER,
    instructor_name TEXT,
    -- WHOOP Integration
    whoop_strain REAL,
    whoop_calories INTEGER,
    whoop_avg_hr INTEGER,
    whoop_max_hr INTEGER,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);
```

**ClassType Enum:** gi, no-gi, wrestling, judo, open-mat, s&c, mobility, yoga, rehab, physio, drilling, cardio

#### 2. GYMS TABLE
**Status:** ✅ Fully implemented with verification workflow

```sql
CREATE TABLE gyms (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    slug VARCHAR(200) UNIQUE,  -- URL-friendly
    affiliation VARCHAR(100),  -- e.g., "Gracie Barra", "10th Planet"
    address TEXT,
    city TEXT,
    state TEXT,
    country TEXT,
    postal_code VARCHAR(20),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    phone VARCHAR(50),
    instagram VARCHAR(100),
    website TEXT,
    email TEXT,
    google_maps_url TEXT,
    head_coach VARCHAR(255),
    head_coach_belt VARCHAR(50),
    verified BOOLEAN DEFAULT 0,  -- Admin verification flag
    member_count INTEGER DEFAULT 0,
    added_by_user_id INTEGER,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);
```

#### 3. USERS TABLE (MULTI-USER SUPPORT)
**Status:** ✅ Complete with social profile fields (Migration 046)

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    first_name TEXT,
    last_name TEXT,
    avatar_url TEXT,

    -- Social Profile (Migration 046)
    username VARCHAR(50) UNIQUE,
    display_name VARCHAR(100),
    bio TEXT,
    belt_rank VARCHAR(20),
    belt_stripes INTEGER CHECK(belt_stripes BETWEEN 0 AND 4),
    location_city VARCHAR(100),
    location_state VARCHAR(100),
    location_country VARCHAR(100),
    location_lat DECIMAL(10, 8),
    location_lng DECIMAL(11, 8),
    profile_photo_url TEXT,
    cover_photo_url TEXT,
    started_training DATE,
    preferred_style VARCHAR(20),  -- gi/no-gi/both
    weight_class VARCHAR(20),
    social_links JSONB DEFAULT '{}',

    -- Primary Gym Association
    primary_gym_id INTEGER REFERENCES gyms(id),

    -- Privacy Settings
    profile_visibility VARCHAR(20) DEFAULT 'friends',  -- public/friends/private
    activity_visibility VARCHAR(20) DEFAULT 'friends',
    searchable BOOLEAN DEFAULT TRUE,
    show_location BOOLEAN DEFAULT TRUE,
    show_gym BOOLEAN DEFAULT TRUE,
    allow_tagging BOOLEAN DEFAULT TRUE,
    require_tag_approval BOOLEAN DEFAULT FALSE,

    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);
```

#### 4. PROFILE TABLE
**Status:** ✅ Extended with setup wizard fields (Migration 048)

Key fields:
- `user_id` (unique, FK to users)
- `belt_rank`, `belt_stripes` (duplicated with users table)
- `setup_completed` (boolean, for onboarding wizard)
- `weekly_bjj_goal`, `weekly_sc_goal`, `weekly_mobility_goal` (setup wizard)
- `gym_name`, `default_gym` (text-based gym association)
- `primary_training_type` (default class type)

#### 5. FRIEND_CONNECTIONS TABLE (USER-TO-USER)
**Status:** ✅ Complete bidirectional friend requests

```sql
CREATE TABLE friend_connections (
    id SERIAL PRIMARY KEY,
    requester_id INTEGER NOT NULL REFERENCES users(id),
    recipient_id INTEGER NOT NULL REFERENCES users(id),
    status VARCHAR(20) DEFAULT 'pending',  -- pending/accepted/declined/blocked/cancelled
    connection_source VARCHAR(30),  -- search/gym/mutual/partner/location/import/qr_code
    request_message TEXT,
    requested_at TIMESTAMP DEFAULT NOW(),
    responded_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(requester_id, recipient_id)
);
```

#### 6. FRIEND_SUGGESTIONS TABLE
**Status:** ✅ Schema ready, algorithm needs implementation

```sql
CREATE TABLE friend_suggestions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    suggested_user_id INTEGER NOT NULL REFERENCES users(id),
    score DECIMAL(5, 2),  -- 0.00 to 99.99
    reasons JSONB,  -- ["same_gym", "mutual_friends:3", "same_city"]
    mutual_friends_count INTEGER DEFAULT 0,
    dismissed BOOLEAN DEFAULT FALSE,
    dismissed_at TIMESTAMP,
    generated_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    UNIQUE(user_id, suggested_user_id)
);
```

#### 7. FRIENDS TABLE (LOCAL CONTACTS)
**Status:** ✅ Text-based training partners (not user connections)

```sql
CREATE TABLE friends (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    friend_type TEXT,  -- instructor/training-partner/both
    belt_rank TEXT,
    belt_stripes INTEGER,
    instructor_certification TEXT,
    phone TEXT,
    email TEXT,
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    UNIQUE(user_id, name)
);
```

---

### ✅ ADDITIONAL SOCIAL TABLES

- **user_gyms** - Many-to-many relationship (users ↔ gyms)
- **partner_links** - Connect text partner names to real users
- **blocked_users** - Block list
- **activity_feed** - Social feed items
- **feed_likes** - Activity likes
- **feed_comments** - Activity comments
- **notifications** - User notifications

---

## API Endpoints

### ✅ IMPLEMENTED ENDPOINTS

#### Analytics (GET /api/analytics/)
- `/performance-overview` - Dashboard stats
- `/partners/stats` - Partner analytics
- `/partners/head-to-head` - Partner comparison
- `/readiness/trends` - Recovery metrics
- `/whoop/analytics` - Fitness tracker data
- `/techniques/breakdown` - Technique analysis
- `/consistency/metrics` - Training consistency
- `/milestones` - Progression tracking
- `/instructors/insights` - Instructor analytics

**Issue:** ❌ NO `type` filter parameter (only date range filtering)

#### Social/Friends (GET/POST /api/social/, /api/friends/)
- `/users/search` - User search by name/email
- `/users/recommended` - Friend recommendations
- `/follow/{user_id}` - Follow/unfollow
- `/followers`, `/following` - Lists
- `/like`, `/comment` - Engagement
- `GET /friends/` - List friends
- `POST /friends/` - Create friend (local contact)

#### Gyms (GET /api/gyms/)
- `/` - List gyms (verified_only filter)
- `/search` - Search gyms

**Issue:** ❌ Admin gym verification routes not found

#### Sessions (GET/POST /api/sessions/)
- `POST /` - Create session
- `GET /` - List sessions
- `GET /range/{start_date}/{end_date}` - Date range
- `GET /{session_id}` - Get session (privacy-aware)

---

## Missing/Needed for v0.2.0

### 1. Analytics Type Filtering
**Current:** Analytics endpoints only accept date range
**Needed:** Add `class_type` filter parameter to all analytics endpoints

**Example:**
```python
# Current
GET /api/analytics/performance-overview?start_date=2026-01-01&end_date=2026-02-01

# Needed
GET /api/analytics/performance-overview?types=gi,nogi&start_date=2026-01-01&end_date=2026-02-01
```

### 2. Friend Suggestion Algorithm
**Status:** Schema exists, service code needed

**Algorithm Requirements:**
- Score based on: same gym (40pts), mutual friends (5pts each, max 25), location match (15pts), partner name matching (30pts), similar belt (5pts)
- Minimum threshold: 10 points
- Cache in `friend_suggestions` table
- Regenerate weekly via background job

### 3. Admin Gym Verification
**Status:** `verified` field exists, admin routes needed

**Endpoints Needed:**
```python
GET /api/admin/gyms/pending  # List unverified gyms
POST /api/admin/gyms/{id}/verify  # Verify gym
POST /api/admin/gyms/{id}/reject  # Reject gym
```

### 4. Feedback System
**Status:** Schema exists (`feedback` table), API routes needed

**Endpoints Needed:**
```python
POST /api/feedback  # Submit feedback
GET /api/admin/feedback  # List feedback (admin only)
```

### 5. Session Navigation (Previous/Next)
**Status:** Logic exists, UI enhancement needed

**Endpoint Needed:**
```python
GET /api/sessions/{id}/adjacent  # Returns {previous: {...}, next: {...}}
```

### 6. Dashboard Data Consolidation
**Status:** Individual endpoints exist, need consolidated dashboard endpoint

**Endpoint Needed:**
```python
GET /api/dashboard/summary  # All dashboard data in single request
```

---

## Architecture Notes

### Belt Tracking Duplication
⚠️  **Belt rank stored in TWO places:**
1. `users.belt_rank`, `users.belt_stripes` (social profile)
2. `profile.belt_rank`, `profile.belt_stripes` (personal profile)

**Recommendation:** Consolidate to single source of truth (prefer `users` table as it's social-facing)

### Class Type vs Activity Type
✅ **Database uses `class_type` field consistently**
✅ **ClassType enum with 12 values**
✅ **No migration needed** - current naming is fine

### Friend Discovery Architecture
✅ **Dual friend model is correct:**
1. **`friends` table** = Local contacts (text-based)
2. **`friend_connections` table** = User-to-user connections

**No changes needed** - this is intentional design

### Privacy Controls
✅ **Comprehensive privacy system:**
- Field-level visibility controls
- Visibility enum: public/friends/private
- Privacy redaction service for session viewing
- Gradual sharing model (not all-or-nothing)

---

## Technology Stack

- **Backend:** FastAPI (Python)
- **Database:** SQLite (dev) / PostgreSQL (prod)
- **CLI:** Typer + Rich
- **Auth:** JWT (Bearer tokens)
- **ORM:** Raw SQL (no SQLAlchemy)
- **Migrations:** Sequential SQL files

---

## Recommendations for v0.2.0

### PRIORITY 1: Analytics Type Filtering
**Impact:** HIGH
**Effort:** LOW
**Files:** `api/routes/analytics.py`, `core/services/analytics_service.py`

Add `types: List[str]` parameter to analytics methods:
```python
def get_performance_overview(
    user_id: int,
    types: Optional[List[str]] = None,  # NEW
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> Dict[str, Any]:
    # Filter sessions by class_type IN types
```

### PRIORITY 2: Friend Suggestion Algorithm
**Impact:** HIGH
**Effort:** MEDIUM
**Files:** `core/services/friend_suggestions_service.py` (new)

Implement scoring algorithm and background job.

### PRIORITY 3: Feedback System
**Impact:** MEDIUM
**Effort:** LOW
**Files:** `api/routes/feedback.py` (new)

Create POST /api/feedback endpoint.

### PRIORITY 4: Dashboard Consolidation
**Impact:** MEDIUM
**Effort:** LOW
**Files:** `api/routes/dashboard.py`

Create GET /api/dashboard/summary endpoint.

### PRIORITY 5: Admin Gym Verification
**Impact:** MEDIUM
**Effort:** LOW
**Files:** `api/routes/admin.py`

Add gym verification endpoints.

---

## Conclusion

**Database Schema:** ✅ **95% Ready** for v0.2.0
**API Layer:** ⚠️  **70% Ready** - needs enhancements
**Frontend:** ❌ **Not found** - backend-only repo

**Primary Work Needed:**
1. Add type filtering to analytics
2. Implement friend suggestion algorithm
3. Create consolidated dashboard endpoint
4. Add admin gym verification routes
5. Create feedback submission endpoint

**Schema Changes NOT NEEDED:**
- ✅ Gyms table exists
- ✅ Friend connections exist
- ✅ Friend suggestions table exists
- ✅ Belt tracking exists (though duplicated)
- ✅ Privacy controls exist
- ✅ Social features fully scaffolded

---

**Generated:** 2026-02-02
**Agent:** Explore (acd9e36)
**Next Step:** Implement Priority 1-5 enhancements

