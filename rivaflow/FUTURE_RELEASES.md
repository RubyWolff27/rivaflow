# Future Release Roadmap

## Deferred Features & Improvements

### High Priority (P1)

#### UUID Migration Path
**Status:** Deferred from v0.1 scope
**Effort:** 4 hours
**Priority:** P1 (required for multi-user/social features)

**Description:**
Migrate from integer primary keys to UUIDs for all core entities to support future distributed/multi-user scenarios.

**Implementation Plan:**
- Add uuid columns to sessions, readiness, techniques, contacts, gradings tables
- Populate UUIDs for existing records via migration
- Create dual-column period where both id (int) and uuid exist
- Update all foreign key relationships to reference UUIDs
- API endpoints accept both id and uuid during transition
- Final migration to remove integer id columns

**Files to modify:**
- `db/migrations/0XX_add_uuids.sql` (new)
- `db/repositories/*.py` (all repos)
- `api/routes/*.py` (all routes)
- Core services layer

**Breaking changes:**
- API responses will eventually use UUIDs instead of integer IDs
- Requires coordinated frontend/backend update

**Benefits:**
- Enables distributed ID generation
- Better for multi-tenant architecture
- Standard for social/sharing features
- Prevents sequential ID enumeration attacks

---

### Completed (Moved from P2)

#### ✅ Color System Implementation
**Status:** ✅ IMPLEMENTED
**Completed:** January 25, 2026
**Effort:** 1 hour (actual)

**Implementation:**
- Added CSS Variables in `web/src/index.css` for all design tokens
- Updated `web/tailwind.config.js` with Kinetic Teal and Vault color palettes
- Created `web/COLOR_SYSTEM.md` comprehensive documentation
- Implemented border radius standards (8px buttons, 12px cards)
- All accessibility requirements met (3:1 UI, 4.5:1 text contrast)
- Component classes updated: `.btn-primary`, `.card`, `.input`
- Added utilities: `.text-kinetic`, `.bg-kinetic`, `.rounded-button`, `.rounded-card`

**Design Tokens Implemented:**
```css
--color-bg-primary: #F4F7F5 (light) / #0A0C10 (dark) ✓
--color-bg-secondary: #FFFFFF (light) / #1A1E26 (dark) ✓
--color-text-primary: #0A0C10 (light) / #F4F7F5 (dark) ✓
--color-text-secondary: #64748B (light) / #94A3B8 (dark) ✓
--color-brand-accent: #00F5D4 (Kinetic Teal) ✓
--color-border: #E2E8F0 (light) / #2D343E (dark) ✓
```

---

### Medium Priority (P2)

#### Social Features - Friend Discovery & Activity Feed (Strava-style)
**Status:** Deferred - Not worth effort until ~100+ active users
**Effort:** 40-60 hours (full implementation)
**Priority:** P2 (defer until user base grows)

**Description:**
Complete social network features for BJJ community building - friend discovery, connections, activity feed, and partner linking. Based on comprehensive PRD.

**Why Deferred:**
- Friend discovery algorithms are overkill with <100 users (manual search sufficient)
- Activity feeds have little value with few friends to follow
- Suggestion scoring complex but unnecessary at small scale
- High development + maintenance cost for limited ROI
- Better to focus on core training features and user retention first

**When to Implement:**
- **Trigger:** 100+ monthly active users OR strong user demand for social features
- **Signal:** Users manually asking "who else from my gym is on RivaFlow?"

**Phase 1: Foundation (8 hours)** ✅ Partially Complete
- Database schema with enhanced profiles ✅ DONE (migration 046)
- Friend connections repository ✅ DONE (social_connection_repo.py)
- Basic profile fields: username, belt_rank, location ✅ DONE
- **Status:** Schema exists but no APIs/UI implemented

**Phase 2: Friend Discovery (12 hours)**
- Friend suggestion algorithm with scoring:
  - Same gym (40 pts), mutual friends (25 pts), partner match (30 pts), location (15 pts)
- API endpoints for search, friend requests, accept/decline
- Privacy filtering (blocked users, visibility settings)
- Partner text matching (fuzzy match "John" in sessions to @john_bjj user)

**Phase 3: Activity Feed (12 hours)**
- Auto-generate feed items when logging sessions
- Like/comment on friend activities
- Privacy-filtered feed (friends-only visibility)
- Milestone sharing (belt promotions, 100 hours, streaks)

**Phase 4: UI/UX (16 hours)**
- Profile pages (/profile/:username)
- Find Friends page (suggestions, search, gym-based)
- Friends list management
- Activity feed with infinite scroll
- Friend requests (accept/decline)

**Phase 5: Advanced Features (12 hours)**
- Partner linking flow (suggest linking text partners to users)
- Gym-based groups/communities
- Training stats comparisons (opt-in leaderboards)
- QR code friend adding (in-person at gym)

**Database Schema (Already Exists):**
- Enhanced users table (username, belt_rank, location, privacy settings)
- Enhanced gyms table (slug, affiliation, coordinates)
- friend_connections, blocked_users, friend_suggestions
- activity_feed, feed_likes, feed_comments
- partner_links, user_gyms

**Files Created (Not Yet Used):**
- `db/migrations/046_social_features_comprehensive_pg.sql` ✅
- `db/repositories/social_connection_repo.py` ✅
- APIs: Pending (social_profile.py, social_connections.py, social_feed.py)
- Frontend: Pending (Profile.tsx, FindFriends.tsx, SocialFeed.tsx)

**Decision:** Keep migration 046 (safe, adds useful profile fields even without social features). Defer API/UI implementation until user base justifies effort.

**See:** Full PRD in chat history with detailed specs, privacy model, and suggestion algorithm.

---

### Future Enhancements

#### Goal Completion Celebrations
**Effort:** 1 hour
**Description:** Add visual celebration when weekly goals are completed (confetti, sound, badge unlock)

#### Goal History Page
**Effort:** 2 hours
**Description:** Dedicated page showing goal completion history over time with trend charts

#### Goals Visualization in Reports
**Effort:** 2 hours
**Description:** Add line chart to Reports page showing 12-week goal completion trend

#### Streak Milestones
**Effort:** 1 hour
**Description:** Highlight streak milestones (5-day, 10-day, month, 100-day) with badges/notifications

#### Technique Focus Planning
**Status:** Plan exists in `/Users/rubertwolff/.claude/plans/virtual-swinging-metcalfe.md`
**Effort:** 6 hours
**Description:** Restructure session logging to track "Technique of the Day" with detailed notes and media URLs

#### AI Video Analysis & Feedback
**Effort:** 8-12 hours
**Description:** Integrate AI-powered video analysis to provide technique feedback and insights on instructional videos

**Features:**
- Analyze instructional videos for technique breakdown and key moments
- Auto-generate timestamps for technique phases (setup, entry, control, finish)
- Provide technique critique and common mistakes to watch for
- Suggest related techniques and progressions
- Generate searchable transcripts and summaries
- Identify skill level (beginner/intermediate/advanced)
- Extract drills and training recommendations

**Technical Approach:**
- Use Claude API with vision capabilities for video frame analysis
- Process videos in chunks to stay within token limits
- Cache analysis results to avoid re-processing
- Allow users to regenerate analysis with different prompts
- Store AI-generated insights alongside video metadata

**Implementation:**
- Add `ai_analysis` JSON field to videos table
- Create background job queue for video processing
- Add "Analyze Video" button in UI
- Display AI insights in expandable section on video cards
- Allow editing/refining AI-generated timestamps

**Benefits:**
- Dramatically improves video library value
- Helps users quickly understand technique concepts
- Reduces time spent manually creating timestamps
- Enables better video search and discovery
- Provides coaching insights without human instructor

---

## Completed in v0.1

✅ Fix subs_per_class calculation bug
✅ Add terminal tables to CLI reports with color coding
✅ Add Quick Session Log widget to Dashboard
✅ Create Privacy Redaction Service (P0 critical)
✅ Add Weekly Goals & Streak Tracking
✅ Readiness Trend Visualization (already existed)
✅ Test Suite Foundation (in progress - Item #8)

---

## Notes

- UUID migration is critical path for social features but can be deferred until multi-user support is prioritized
- Color system is cosmetic but improves brand consistency
- All future enhancements should maintain test coverage >80%
